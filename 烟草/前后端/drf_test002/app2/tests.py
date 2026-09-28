import io
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .models import Fer_region_record, LandParcel, NutrientDeficiency, Pesticide_record, Role, User, UserRole


class UnifiedDetectionWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="demo", password="demo", phone="13800000000")
        self.field = LandParcel.objects.create(user=self.user, name="test field", area=1000)
        self.user.token = "test-token"
        self.user.save(update_fields=["token"])
        UserRole.objects.create(user=self.user, role=Role.objects.get(code="grower"), is_primary=True)
        self.auth = {"HTTP_AUTHORIZATION": "Bearer test-token"}

    def test_all_detected_diseases_can_create_records(self):
        diseases = ["白星病", "花叶病", "烟青虫", "野火病"]
        image = io.BytesIO()
        Image.new("RGB", (4, 4), "green").save(image, format="PNG")
        image.seek(0)

        with patch("app2.views.unified_detection._run_unified_detection") as detect:
            detect.return_value = ({
                "diseases": diseases,
                "is_healthy": False,
                "is_deficiency_k": False,
                "all_detected": diseases,
                "confidence": {name: 0.9 for name in diseases},
            }, None)
            result = self.client.post(
                reverse("unified-detection-with-field", args=[self.user.id, self.field.id]),
                {"image": image},
                format="multipart",
                **self.auth,
            )

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["result"]["diseases"], diseases)

        result = self.client.post(
            reverse("pesticide_from_diseases", args=[self.user.id, self.field.id]),
            {"disease_types": diseases},
            content_type="application/json",
            **self.auth,
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["created"], 4)
        self.assertEqual(
            set(Pesticide_record.objects.values_list("target_pest", flat=True)),
            set(diseases),
        )

    def test_strategy_context_reports_created_diseases(self):
        Pesticide_record.objects.create(
            field_id=self.field,
            record_num=1,
            pesticide_name="待农技人员确认",
            target_pest="野火病",
            dosage=0,
            unit="",
        )
        result = self.client.get(
            reverse("field-strategy-context", args=[self.user.id, self.field.id]), **self.auth
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["data"]["disease_types"], ["野火病"])

    def test_image_k_hint_does_not_create_nutrient_or_fertilizer_record(self):
        image = io.BytesIO()
        Image.new("RGB", (4, 4), "green").save(image, format="PNG")
        image.seek(0)
        with patch("app2.views.unified_detection._run_unified_detection") as detect:
            detect.return_value = ({
                "diseases": [], "is_healthy": False, "is_deficiency_k": True,
                "all_detected": ["缺钾"], "confidence": {"缺钾": 0.9},
            }, None)
            result = self.client.post(
                reverse("unified-detection-with-field", args=[self.user.id, self.field.id]),
                {"image": image},
                **self.auth,
            )
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()["requires_confirmation"])
        self.assertEqual(NutrientDeficiency.objects.count(), 0)
        self.assertEqual(Fer_region_record.objects.count(), 0)

    def test_confirmed_nutrient_requires_login_token_and_evidence(self):
        url = reverse("confirmed-deficiency", args=[self.user.id, self.field.id])
        payload = {"nutrient_type": "P", "verification_source": "lab_report",
                   "verification_reference": "report-2026-001"}
        self.assertEqual(self.client.post(url, payload).status_code, 403)
        self.user.token = "test-token"
        self.user.save(update_fields=["token"])
        self.assertEqual(self.client.post(url, {**payload, "verification_reference": ""},
                                          HTTP_X_USER_TOKEN="test-token").status_code, 400)
        self.assertEqual(NutrientDeficiency.objects.count(), 0)
        result = self.client.post(url, payload, HTTP_X_USER_TOKEN="test-token")
        self.assertEqual(result.status_code, 201)
        record = NutrientDeficiency.objects.get()
        self.assertEqual(record.nutrient_type, "P")
        self.assertIsNone(record.intensity)
        self.assertEqual(record.verification_reference, "report-2026-001")
        self.assertEqual(Fer_region_record.objects.count(), 0)
        fertilizer_url = reverse("fer-region-crud", args=[self.user.id, self.field.id])
        fertilizer_result = self.client.post(fertilizer_url, **self.auth)
        self.assertEqual(fertilizer_result.json()["code"], 404)
        self.assertEqual(Fer_region_record.objects.count(), 0)
