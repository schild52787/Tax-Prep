from app.pdf.field_mappings.form_1040_fields import FORM_1040_FIELDS
from app.pdf.field_mappings.schedule_a_fields import SCHEDULE_A_FIELDS
from app.pdf.field_mappings.schedule_b_fields import SCHEDULE_B_FIELDS
from app.pdf.field_mappings.schedule_d_fields import SCHEDULE_D_FIELDS

FIELD_MAPS = {
    "form_1040": FORM_1040_FIELDS,
    "schedule_a": SCHEDULE_A_FIELDS,
    "schedule_b": SCHEDULE_B_FIELDS,
    "schedule_d": SCHEDULE_D_FIELDS,
}


def get_field_map(form_id: str) -> dict:
    return FIELD_MAPS.get(form_id, {})
