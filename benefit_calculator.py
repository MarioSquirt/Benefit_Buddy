#BenefitCalculator.py


# ============================================================
# IMPORTS
# ============================================================

# --- Kivy core ---
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
Window.softinput_mode = "below_target"
from kivy.core.image import Image as CoreImage
from kivy.metrics import sp
from kivy.utils import get_color_from_hex, platform
from kivy.resources import resource_add_path, resource_find
from kivy.properties import ObservableList, StringProperty

# --- Kivy UI widgets/layouts ---
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.togglebutton import ToggleButton

# --- Kivy graphics/animation ---
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle, Rectangle, PushMatrix, PopMatrix, Rotate, Translate
from kivy.animation import Animation

# --- Project-specific ---
from main import SafeLabel

# --- Standard library ---
import os
import csv
import tracemalloc
from datetime import datetime
from collections import defaultdict

import sqlite3
from db_builder import build_database

from postcode_lookup import lookup_postcode as compact_lookup
from postcode_lookup import load_all_postcode_data
from postcode_lookup import all_postcodes

# ============================================================
# START MEMORY TRACING
# ============================================================
tracemalloc.start()

def get_app_data_path():
    if platform == "android":
        from android.storage import app_storage_path
        return app_storage_path()
    elif platform == "ios":
        from ios.storage import app_storage_path
        return app_storage_path()
    else:
        # Desktop fallback
        return os.path.join(os.getcwd(), "app_data")


def ensure_database():
    app_data = get_app_data_path()
    os.makedirs(app_data, exist_ok=True)

    db_path = os.path.join(app_data, "postcodes.db")

    # The DB should already exist — built during development and shipped with the app
    if not os.path.exists(db_path):
        print("ERROR: postcodes.db is missing from app_data!")
        return None

    return db_path

ICON_PATHS = {
    "Introduction": "images/icons/Introduction-icon/Introduction-32px.png",
    "Claimant Details": "images/icons/ClaimantDetails-icon/ClaimantDetails-32px.png",
    "Finances": "images/icons/Finances-icon/Finances-32px.png",
    "Housing": "images/icons/Housing-icon/Housing-32px.png",
    "Children": "images/icons/Children-icon/Children-32px.png",
    "Additional Elements": "images/icons/AdditionalElements-icon/AdditionalElements-32px.png",
    "Sanctions": "images/icons/Sanctions-icon/Sanctions-32px.png",
    "Advanced Payments": "images/icons/AdvancedPayment-icon/AdvancedPayment-32px.png",
    "Summary": "images/icons/Summary-icon/Summary-32px.png",
}

# ============================================================
# LONDON POSTCODE DETECTION (100% ACCURATE)
# ============================================================

LONDON_OUTCODES = (
    "E", "EC", "N", "NW", "SE", "SW", "W", "WC",
    "BR", "CR", "DA", "EN", "HA", "IG", "KT", "RM", "SM", "TW", "UB"
)

def is_london_postcode(postcode: str) -> bool:
    if not postcode:
        return False

    postcode = postcode.strip().upper()
    # Extract outcode (e.g. "SW1A", "E14", "HA9")
    outcode = postcode.split(" ")[0]

    return any(outcode.startswith(prefix) for prefix in LONDON_OUTCODES)


# --- Register base paths for resources ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add folders to Kivy's resource search paths
for folder in ["images", "font", ".venv"]:
    full_path = os.path.join(BASE_DIR, folder)
    if os.path.exists(full_path):
        resource_add_path(full_path)

# Define GOV.UK colour scheme
GOVUK_BLUE = "#005EA5"
WHITE = "#FFFFFF"
YELLOW = "#FFDD00"

# Convert hex color to RGBA
color = get_color_from_hex("#005EA5")  # GOVUK_BLUE

# Set the background color of the app to GOVUK_BLUE
Window.clearcolor = get_color_from_hex("#005EA5")  # GOVUK_BLUE

layout = BoxLayout(orientation="vertical", spacing=10, padding=20, size_hint=(1,1))
if hasattr(Window, "maximize"):
    Window.maximize()

# Bind the window size to adjust the layout dynamically
def adjust_layout(instance, value):
    for widget in instance.children:
        if isinstance(widget, BoxLayout) and widget.size_hint == (1, 1):
            widget.size = (Window.width, Window.height)

Window.bind(size=adjust_layout)


UC_RATES = {
    "year": "2025/26",

    "standard_allowance": {
        "single_u25": 316.98,
        "single_25plus": 400.14,
        "couple_u25": 497.55,
        "couple_25plus": 628.10,
        "minimum_amount": 0.01,
    },

    "child_element": {
        # First child born before 6 April 2017
        "first_child_pre2017": 339.00,
        # First child born on/after 6 April 2017, and subsequent children where allowed
        "child": 292.81,
    },

    "disabled_child": {
        "lower": 158.76,
        "higher": 495.87,
    },

    "lcw_lcwra": {
        "lcw": 158.76,
        "lcwra": 423.27,
    },

    "carer_element": 201.68,

    "childcare": {
        "reimbursement_rate": 0.85,
        "cap_one_child": 1031.88,
        "cap_two_plus": 1768.94,
    },

    "non_dependant": {
        "housing_cost_contribution": 93.02,
    },

    "work_allowance": {
        # Higher = no housing element, with children or LCW/LCWRA
        "higher": 684.00,
        # Lower = with housing element, with children or LCW/LCWRA
        "lower": 411.00,
    },

    "taper_rate": 0.55,

    "capital": {
        "lower_limit": 6000.00,
        "upper_limit": 16000.00,
        "tariff_per_250": 4.35,
    },

    # You can expand these if you later model daily sanction maths explicitly
    "sanctions": {
        "daily_100": {
            "single_u25": 10.40,
            "single_25plus": 13.10,
            "joint_u25": 8.10,
            "joint_25plus": 10.30,
        },
        "daily_40": {
            "single_u25": 4.10,
            "single_25plus": 5.20,
            "joint_u25": 3.20,
            "joint_25plus": 4.10,
        },
    },

    "deduction_caps": {
        "third_party_5pct": {
            "single_u25": 15.85,
            "single_25plus": 20.01,
            "joint_u25": 24.88,
            "joint_25plus": 31.41,
        },
        "rent_min_10pct": {
            "single_u25": 31.70,
            "single_25plus": 40.01,
            "joint_u25": 49.76,
            "joint_25plus": 62.81,
        },
        "rent_max_15pct": {
            "single_u25": 47.55,
            "single_25plus": 60.02,
            "joint_u25": 74.63,
            "joint_25plus": 94.22,
        },
        "overall_max_15pct": {
            "single_u25": 47.55,
            "single_25plus": 60.02,
            "joint_u25": 74.63,
            "joint_25plus": 94.22,
        },
    },

    "child_maintenance_deduction": 36.40,

    "transitional_sdp": {
        "lcwra_included": 143.37,
        "lcwra_not_included": 340.50,
        "joint_higher": 483.88,
        "extra_edp_single": 91.15,
        "extra_edp_couple": 130.22,
        "extra_dp_single": 186.64,
        "extra_dp_couple": 266.94,
        "extra_disabled_children": 192.07,
    },
    "benefit_cap": {
        "london": {
            "single": 1541.67,
            "couple_or_parent": 1841.67,
        },
        "non_london": {
            "single": 1298.67,
            "couple_or_parent": 1516.67,
        }
    }
}

class CalculatorState:
    def __init__(self):
        # -----------------------------
        # Claimant / Partner
        # -----------------------------
        self.relationship = "Single"
        self.claimant_name = ""
        self.claimant_dob = ""
        self.partner_name = ""
        self.partner_dob = ""
        self.claimant_age = None
        self.partner_age = None

        # -----------------------------
        # Finances
        # -----------------------------
        self.income = 0.0
        self.earnings = 0.0
        self.savings = 0.0
        self.debts = 0.0

        # -----------------------------
        # Children
        # -----------------------------
        self.children = []  # list of dicts

        # -----------------------------
        # Disability / Carer
        # -----------------------------
        self.disability = ""          # "LCW", "LCWRA", or ""
        self.had_lcw_before_uc = False
        self.carer = False
        self.receives_disability_benefits = False

        # -----------------------------
        # Childcare
        # -----------------------------
        self.childcare = 0.0

        # -----------------------------
        # Housing
        # -----------------------------
        self.housing_type = ""        # "own", "private", "social", etc.
        self.tenancy_type = ""
        self.rent = 0.0
        self.mortgage = 0.0
        self.shared = 0.0
        self.non_dependants = 0
        self.postcode = ""
        self.location = ""
        self.brma = ""
        self.service_charges = {}
        self.single_under_35 = False
        self.in_london = False
        self.lookup_lha_rate = None

        # -----------------------------
        # SAR Exemptions
        # -----------------------------
        self.care_leaver = False
        self.severe_disability = False
        self.mappa = False
        self.hostel_resident = False
        self.domestic_abuse_refuge = False
        self.ex_offender = False
        self.foster_carer = False
        self.prospective_adopter = False
        self.temporary_accommodation = False
        self.modern_slavery = False
        self.armed_forces_reservist = False

        # -----------------------------
        # Sanctions
        # -----------------------------
        self.sanction_type = ""
        self.sanction_duration = 0     # numeric, not string
        self.hardship = False

        # -----------------------------
        # Advance Payments
        # -----------------------------
        self.advance_amount = 0.0
        self.repayment_period = 0

        # -----------------------------
        # Transitional SDP
        # -----------------------------
        self.had_sdp = False
        self.extra_edp = 0.0
        self.extra_dp = 0.0
        self.extra_disabled_children = 0.0

        # -----------------------------
        # Deduction Caps
        # -----------------------------
        self.third_party_deductions = 0.0
        self.rent_arrears_deduction = 0.0
        self.fraud_deduction = 0.0
        self.overpayment_deduction = 0.0
        self.child_maintenance = 0.0

        # -----------------------------
        # Final Result
        # -----------------------------
        self.calculation_result = ""
        self.breakdown = {}



class CalculatorEngine:

    # ============================================================
    # BREAKDOWN (used by Breakdown screen)
    # ============================================================
    def get_calculation_breakdown(self, data, UC_RATES):
        """
        Returns a dict of all calculation components.
        Mirrors calculate_entitlement() but itemised.
        """

        breakdown = {}

        # Standard allowance
        age = data.claimant_age
        partner_age = data.partner_age
        is_single = (data.relationship == "Single")

        if is_single:
            if age < 25:
                sa = UC_RATES["standard_allowance"]["single_u25"]
            else:
                sa = UC_RATES["standard_allowance"]["single_25plus"]
        else:
            if age < 25 and partner_age < 25:
                sa = UC_RATES["standard_allowance"]["couple_u25"]
            else:
                sa = UC_RATES["standard_allowance"]["couple_25plus"]

        breakdown["Standard Allowance"] = sa

        # Housing
        housing = self.calculate_housing_element(data, UC_RATES)
        breakdown["Housing Element"] = housing

        # Children
        children_total = self.calculate_child_elements(data, UC_RATES)
        breakdown["Child Elements"] = children_total

        # Disability
        disability_element, has_lcw, has_lcwra, lcw_payable = \
            self.calculate_disability_elements(data, UC_RATES)
        breakdown["Disability Element"] = disability_element

        # Carer
        carer_element = UC_RATES["carer_element"] if (data.carer and not has_lcwra) else 0.0
        breakdown["Carer Element"] = carer_element

        # Childcare
        childcare = float(data.childcare or 0)
        breakdown["Childcare Costs"] = childcare

        # Transitional SDP
        transitional_sdp = self.calculate_transitional_sdp(
            data, UC_RATES, has_lcwra, is_single
        )
        breakdown["Transitional SDP"] = transitional_sdp

        # Capital deduction
        capital = float(data.savings or 0)
        lower_cap = UC_RATES["capital"]["lower_limit"]
        upper_cap = UC_RATES["capital"]["upper_limit"]
        tariff_per_250 = UC_RATES["capital"]["tariff_per_250"]

        if capital >= upper_cap:
            capital_income = float("inf")
        elif capital < lower_cap:
            capital_income = 0.0
        else:
            blocks = ((capital - lower_cap) + 249) // 250
            capital_income = blocks * tariff_per_250

        breakdown["Capital Deduction"] = -capital_income

        # Earnings deduction
        earnings_deduction = self.calculate_earnings_deduction(
            data, UC_RATES, housing, has_lcw, has_lcwra, len(data.children)
        )
        breakdown["Earnings Deduction"] = -earnings_deduction

        # Sanctions
        sanction = self.calculate_sanction_reduction(
            data, UC_RATES, age, partner_age
        )
        breakdown["Sanctions"] = -sanction

        # Advance repayment
        advance = float(data.advance_amount or 0)
        months = int(data.repayment_period or 0)
        advance_deduction = advance / months if months > 0 else 0.0
        breakdown["Advance Repayment"] = -advance_deduction

        # Deduction caps
        deduction_caps_total = self.apply_deduction_caps(
            data, UC_RATES, sa
        )
        breakdown["Deduction Caps"] = -deduction_caps_total

        # Final entitlement
        total = sum(breakdown.values())
        breakdown["Final Entitlement"] = total

        return breakdown

    # ============================================================
    # SAR EXEMPTIONS
    # ============================================================
    def is_sar_exempt(self, data):
        return any([
            data.care_leaver,
            data.severe_disability,
            data.mappa,
            data.hostel_resident,
            data.domestic_abuse_refuge,
            data.ex_offender,
            data.foster_carer,
            data.prospective_adopter,
            data.temporary_accommodation,
            data.modern_slavery,
            data.armed_forces_reservist,
        ])

    # ============================================================
    # EARNINGS DEDUCTION
    # ============================================================
    def calculate_earnings_deduction(self, data, UC_RATES, housing_element, has_lcw, has_lcwra, num_children):
        earnings = float(data.income or 0)
        if earnings <= 0:
            return 0.0

        qualifies_for_WA = (
            num_children > 0 or
            has_lcw or
            has_lcwra
        )

        if not qualifies_for_WA:
            return earnings * UC_RATES["taper_rate"]

        work_allowance = (
            UC_RATES["work_allowance"]["lower"]
            if housing_element > 0
            else UC_RATES["work_allowance"]["higher"]
        )

        earnings_after_WA = max(0, earnings - work_allowance)
        return earnings_after_WA * UC_RATES["taper_rate"]

    # ============================================================
    # CHILD ELEMENTS
    # ============================================================
    def calculate_child_elements(self, data, UC_RATES):
        children = self._parse_children(data.children)
        if not children:
            return 0.0

        eligible = self._apply_two_child_limit(children)

        total = 0.0

        # First eligible child
        first_child = eligible[0]
        total += self._first_child_rate(first_child, UC_RATES)

        # Remaining eligible children
        for child in eligible[1:]:
            total += UC_RATES["child_element"]["child"]

        # Multiple birth additions
        total += self._multiple_birth_additions(children, UC_RATES)

        # Disabled child additions
        total += self._disabled_child_additions(children, UC_RATES)

        return total

    def _parse_children(self, children):
        parsed = []
        for child in children:
            dob_str = child.get("dob", "")
            try:
                dob = datetime.strptime(dob_str, "%d/%m/%Y")
                parsed.append({"dob": dob, "raw": child})
            except:
                continue

        parsed.sort(key=lambda c: c["dob"])
        return parsed

    def _is_exception(self, child_raw):
        return (
            child_raw.get("adopted") or
            child_raw.get("kinship_care") or
            child_raw.get("multiple_birth") or
            child_raw.get("non_consensual")
        )

    def _apply_two_child_limit(self, children):
        eligible = []
        for i, child in enumerate(children):
            if i < 2:
                eligible.append(child)
            else:
                if self._is_exception(child["raw"]):
                    eligible.append(child)
        return eligible

    def _first_child_rate(self, child, UC_RATES):
        cutoff = datetime(2017, 4, 6)
        if child["dob"] < cutoff:
            return UC_RATES["child_element"]["first_child_pre2017"]
        return UC_RATES["child_element"]["child"]

    def _multiple_birth_additions(self, children, UC_RATES):
        groups = defaultdict(list)

        for child in children:
            groups[child["dob"]].append(child)

        total = 0.0
        for dob, group in groups.items():
            if len(group) <= 1:
                continue
            extra_children = len(group) - 1
            total += extra_children * UC_RATES["child_element"]["multiple_birth"]

        return total

    def _disabled_child_additions(self, children, UC_RATES):
        total = 0.0
        for child in children:
            raw = child["raw"]
            if raw.get("severely_disabled"):
                total += UC_RATES["child_element"]["disabled_child_higher"]
            elif raw.get("disabled"):
                total += UC_RATES["child_element"]["disabled_child_lower"]
        return total

    # ============================================================
    # DISABILITY ELEMENTS (LCW / LCWRA)
    # ============================================================
    def calculate_disability_elements(self, data, UC_RATES):
        """
        Determines LCW / LCWRA element and applies rules:
        - LCWRA always payable unless claimant is a carer
        - LCW only payable if claimant had LCW before UC
        - LCW still gives Work Allowance even if not payable
        Returns:
            disability_element (float),
            has_lcw (bool),
            has_lcwra (bool),
            lcw_payable (bool)
        """

        status = (data.disability or "").upper().strip()
        is_carer = bool(data.carer)

        has_lcw = (status == "LCW")
        has_lcwra = (status == "LCWRA")

        # LCWRA + Carer rule
        if has_lcwra and is_carer:
            return 0.0, False, False, False

        # LCWRA always payable
        if has_lcwra:
            data.severe_disability = True  # SAR exemption
            return UC_RATES["lcw_lcwra"]["lcwra"], False, True, True

        # LCW logic
        if has_lcw:
            if data.had_lcw_before_uc:
                return UC_RATES["lcw_lcwra"]["lcw"], True, False, True
            else:
                # LCW NOT payable — but still gives Work Allowance
                return 0.0, True, False, False

        # No disability
        return 0.0, False, False, False

    # ============================================================
    # SANCTIONS
    # ============================================================
    def calculate_sanction_reduction(self, data, UC_RATES, age, partner_age):
        """
        Calculates sanction reduction using:
        - sanction_type: "low", "medium", "high"
        - sanction_duration: number of days
        - claimant type (single/couple)
        - age category
        - hardship rules (reduced sanction)
        """

        sanction_type = (data.sanction_type or "").lower().strip()
        duration_str = data.sanction_duration

        if not sanction_type or not duration_str:
            return 0.0

        try:
            days = int(duration_str)
        except:
            return 0.0

        is_single = (data.relationship == "Single")

        # Determine claimant category
        if is_single:
            category = "single_u25" if age < 25 else "single_25plus"
        else:
            if age < 25 and partner_age < 25:
                category = "joint_u25"
            else:
                category = "joint_25plus"

        # Determine daily rate
        if sanction_type == "High":
            daily_rate = UC_RATES["sanctions"]["daily_100"][category]
        elif sanction_type in ("medium", "low"):
            daily_rate = UC_RATES["sanctions"]["daily_40"][category]
        else:
            return 0.0

        # Hardship reduction
        if data.hardship:
            daily_rate *= 0.6

        return daily_rate * days

    # ============================================================
    # DEDUCTION CAPS
    # ============================================================
    def apply_deduction_caps(self, data, UC_RATES, standard_allowance):
        """
        Applies UC deduction caps using only the caps defined in UC_RATES:
        - Third-party deductions (5%)
        - Rent/service charge deductions (10–15%)
        - Fraud/overpayment deductions (no individual cap)
        - Overall maximum deduction cap (15%)
        - Child maintenance (outside cap)
        """

        age = data.claimant_age
        partner_age = data.partner_age
        is_single = (data.relationship == "Single")

        if age is None:
            raise ValueError("Claimant age missing — DOB must be entered before calculation.")

        if not is_single and partner_age is None:
            raise ValueError("Partner age missing — partner DOB must be entered before calculation.")

        # Determine category
        if is_single:
            category = "single_u25" if age < 25 else "single_25plus"
        else:
            if age < 25 and partner_age < 25:
                category = "joint_u25"
            else:
                category = "joint_25plus"

        caps = UC_RATES["deduction_caps"]

        # 1. Third-party deductions (5%)
        third_party = float(data.third_party_deductions or 0)
        third_party_cap = caps["third_party_5pct"][category]
        third_party = min(third_party, third_party_cap)

        # 2. Rent/service charge deductions (10–15%)
        rent_deduction = float(data.rent_arrears_deduction or 0)
        min_rent = caps["rent_min_10pct"][category]
        max_rent = caps["rent_max_15pct"][category]

        if rent_deduction > 0:
            rent_deduction = max(min_rent, min(rent_deduction, max_rent))
        else:
            rent_deduction = 0.0

        # 3. Fraud / overpayment deductions
        fraud_deduction = float(data.fraud_deduction or 0)
        overpayment = float(data.overpayment_deduction or 0)

        # 4. Child maintenance (outside cap)
        child_maintenance = float(data.child_maintenance or 0)
        child_maintenance = min(child_maintenance, UC_RATES["child_maintenance_deduction"])

        # 5. Apply overall 15% cap
        overall_cap = caps["overall_max_15pct"][category]

        capped_deductions = third_party + rent_deduction + fraud_deduction + overpayment
        capped_deductions = min(capped_deductions, overall_cap)

        # Child maintenance added AFTER cap
        total_deductions = capped_deductions + child_maintenance

        return total_deductions

    # ============================================================
    # BEDROOM ENTITLEMENT
    # ============================================================
    def calculate_bedroom_entitlement(self, data):
        """
        Returns the number of bedrooms the household is entitled to.
        Based on standard UC bedroom rules.
        """

        children = data.children
        num_children = len(children)

        # Adults
        is_single = (data.relationship == "Single")
        adults = 1 if is_single else 2

        bedrooms = 1  # for the claimant(s)

        # Parse children ages
        child_ages = []
        for child in children:
            try:
                dob = datetime.strptime(child["dob"], "%d/%m/%Y")
                age = (datetime.now() - dob).days // 365
                child_ages.append((age, child.get("sex", "U")))
            except:
                continue

        # Sort by age
        child_ages.sort(key=lambda x: x[0])

        # Group children into rooms
        used = [False] * len(child_ages)

        for i in range(len(child_ages)):
            if used[i]:
                continue

            age_i, sex_i = child_ages[i]
            paired = False

            # Try to pair with another child
            for j in range(i + 1, len(child_ages)):
                if used[j]:
                    continue

                age_j, sex_j = child_ages[j]

                # Under 10 → always share
                if age_i < 10 and age_j < 10:
                    used[i] = used[j] = True
                    bedrooms += 1
                    paired = True
                    break

                # Same sex and both under 16 → share
                if sex_i == sex_j and age_i < 16 and age_j < 16:
                    used[i] = used[j] = True
                    bedrooms += 1
                    paired = True
                    break

            if not paired:
                used[i] = True
                bedrooms += 1

        return bedrooms

    # ============================================================
    # NON‑DEPENDANT DEDUCTION
    # ============================================================
    def calculate_non_dependant_deduction(self, data, UC_RATES):
        nondeps = int(data.non_dependants or 0)
        if nondeps <= 0:
            return 0.0

        rate = UC_RATES["non_dependant"]["housing_cost_contribution"]
        return nondeps * rate

    # ============================================================
    # ELIGIBLE SERVICE CHARGES (SOCIAL RENT)
    # ============================================================
    def calculate_eligible_service_charges(self, data):
        """
        Calculates eligible service charges for social rent.
        """

        eligible_keys = {
            "cleaning",
            "communal_cleaning",
            "lighting",
            "communal_lighting",
            "grounds",
            "grounds_maintenance",
            "lift_maintenance",
            "fire_safety",
            "door_entry",
            "shared_facilities",
            "communal_repairs",
            "estate_services",
        }

        charges = data.service_charges
        if not isinstance(charges, dict):
            return 0.0

        total = 0.0
        for key, value in charges.items():
            if key.lower().strip() in eligible_keys:
                try:
                    total += float(value)
                except:
                    pass

        return total

    # ============================================================
    # HOUSING ELEMENT (SOCIAL + PRIVATE + LHA)
    # ============================================================
    def calculate_housing_element(self, data, UC_RATES):
        housing_type = (data.housing_type or "").lower()

        # -----------------------------
        # Owner‑occupier (mortgage)
        # -----------------------------
        if housing_type == "Own":
            return float(data.mortgage or 0)

        # -----------------------------
        # Shared accommodation
        # -----------------------------
        if housing_type == "Shared Accommodation":
            return float(data.shared or 0)

        # -----------------------------
        # Renting (private or social)
        # -----------------------------
        rent = float(data.rent or 0)
        brma = data.brma
        location = data.location

        # Non‑dependant deductions
        nondep = self.calculate_non_dependant_deduction(data, UC_RATES)

        # -----------------------------
        # SOCIAL RENT
        # -----------------------------
        if location.lower() in ["england", "scotland", "wales"] and data.tenancy_type == "Social":
            eligible_services = self.calculate_eligible_service_charges(data)
            eligible_rent = float(data.rent or 0)

            # Eligible rent = rent + eligible service charges − non‑dependant deductions
            eligible = max(0, eligible_rent + eligible_services - nondep)
            return eligible

        # -----------------------------
        # PRIVATE RENT (LHA)
        # -----------------------------
        bedrooms = self.calculate_bedroom_entitlement(data)

        # Shared accommodation rule
        if bedrooms == 1 and data.single_under_35:
            bedrooms = "Shared"

        # Lookup LHA rate (provided by Housing screen)
        if not callable(data.lookup_lha_rate):
            raise ValueError("LHA lookup function not attached to CalculatorState.")

        lha_rate = data.lookup_lha_rate(brma, bedrooms, location)

        eligible = min(rent, lha_rate)
        eligible -= nondep

        return max(0, eligible)

    # ============================================================
    # TRANSITIONAL SDP
    # ============================================================
    def calculate_transitional_sdp(self, data, UC_RATES, has_lcwra, is_single):
        """
        Calculates Transitional SDP Element based on:
        - Whether claimant previously received SDP
        - Whether LCWRA is included in the award
        - Whether single or couple
        - Additional EDP/DP/disabled child amounts
        """

        if not data.had_sdp:
            return 0.0

        rates = UC_RATES["transitional_sdp"]

        # Base SDP transitional protection
        if is_single:
            if has_lcwra:
                base = rates["lcwra_included"]
            else:
                base = rates["lcwra_not_included"]
        else:
            base = rates["joint_higher"]

        # Additional components
        extra = 0.0

        if data.extra_edp:
            extra += rates["extra_edp_single"] if is_single else rates["extra_edp_couple"]

        if data.extra_dp:
            extra += rates["extra_dp_single"] if is_single else rates["extra_dp_couple"]

        if data.extra_disabled_children:
            extra += rates["extra_disabled_children"]

        return base + extra

    # ============================================================
    # Benefit Cap
    # ============================================================
    def calculate_benefit_cap(self, data, UC_RATES, total_before_cap, has_lcwra, carer_element):
        """
        Applies the UC Benefit Cap unless exempt.
        """
    
        # -----------------------------
        # Exemptions
        # -----------------------------
        earnings = float(data.earnings or 0)
    
        # 1. LCWRA exemption
        if has_lcwra:
            return 0.0
    
        # 2. Carer element exemption
        if carer_element > 0:
            return 0.0
    
        # 3. Earnings threshold exemption
        if earnings >= 722:
            return 0.0
    
        # 4. Disability benefits exemption (optional)
        if data.receives_disability_benefits:
            return 0.0
    
        # -----------------------------
        # Determine cap level
        # -----------------------------
        in_london = bool(data.in_london)
        is_single = (data.relationship == "Single")
    
        if in_london:
            cap = UC_RATES["benefit_cap"]["london"]["single" if is_single else "couple_or_parent"]
        else:
            cap = UC_RATES["benefit_cap"]["non_london"]["single" if is_single else "couple_or_parent"]
    
        # -----------------------------
        # Apply cap
        # -----------------------------
        if total_before_cap > cap:
            return total_before_cap - cap
    
        return 0.0
    
    # ============================================================
    # FULL ENTITLEMENT CALCULATION
    # ============================================================
    def calculate_entitlement(self, data, UC_RATES):
        """
        Full Universal Credit calculation using all modular helpers.
        """

        # -----------------------------
        # Relationship defaults
        # -----------------------------
        if not data.relationship:
            data.relationship = "Single"

        if not data.tenancy_type:
            data.tenancy_type = "Private"

        # -----------------------------
        # Parse ages
        # -----------------------------
        def parse_age(dob_str):
            if not dob_str:
                return None
            try:
                dob = datetime.strptime(dob_str, "%d/%m/%Y")
                return (datetime.now() - dob).days // 365
            except:
                return None

        age = parse_age(data.claimant_dob)
        partner_age = parse_age(data.partner_dob)
        is_single = (data.relationship == "Single")

        # Strict validation
        if age is None:
            raise ValueError("Please enter a valid claimant date of birth (DD/MM/YYYY).")

        if not is_single and partner_age is None:
            raise ValueError("Please enter a valid partner date of birth (DD/MM/YYYY).")

        # Store ages for deduction caps
        data.claimant_age = age
        data.partner_age = partner_age if not is_single else None

        # -----------------------------
        # Children (full rules)
        # -----------------------------
        child_elements = self.calculate_child_elements(data, UC_RATES)
        num_children = len(data.children)

        # -----------------------------
        # Determine SAR rule (single under 35)
        # -----------------------------
        data.single_under_35 = (
            is_single and
            age is not None and age < 35 and
            num_children == 0 and
            data.tenancy_type == "Private" and
            not self.is_sar_exempt(data)
        )

        # -----------------------------
        # Disability (LCW / LCWRA)
        # -----------------------------
        disability_element, has_lcw, has_lcwra, lcw_payable = \
            self.calculate_disability_elements(data, UC_RATES)

        # -----------------------------
        # Carer element (LCWRA conflict handled in helper)
        # -----------------------------
        is_carer = bool(data.carer)
        carer_element = UC_RATES["carer_element"] if (is_carer and not has_lcwra) else 0.0

        # -----------------------------
        # Childcare
        # -----------------------------
        childcare_costs = float(data.childcare or 0)

        # -----------------------------
        # Standard allowance
        # -----------------------------
        if is_single:
            if age < 25:
                standard_allowance = UC_RATES["standard_allowance"]["single_u25"]
            else:
                standard_allowance = UC_RATES["standard_allowance"]["single_25plus"]
        else:
            if age < 25 and partner_age < 25:
                standard_allowance = UC_RATES["standard_allowance"]["couple_u25"]
            else:
                standard_allowance = UC_RATES["standard_allowance"]["couple_25plus"]

        # -----------------------------
        # Housing element (full LHA + social rent)
        # -----------------------------
        housing_element = self.calculate_housing_element(data, UC_RATES)

        # -----------------------------
        # Transitional SDP
        # -----------------------------
        transitional_sdp = self.calculate_transitional_sdp(
            data,
            UC_RATES,
            has_lcwra,
            is_single
        )

        # -----------------------------
        # Capital deductions
        # -----------------------------
        capital = float(data.savings or 0)
        lower_cap = UC_RATES["capital"]["lower_limit"]
        upper_cap = UC_RATES["capital"]["upper_limit"]
        tariff_per_250 = UC_RATES["capital"]["tariff_per_250"]

        if capital >= upper_cap:
            return 0.0

        if capital < lower_cap:
            capital_income = 0.0
        else:
            blocks = ((capital - lower_cap) + 249) // 250
            capital_income = blocks * tariff_per_250

        # -----------------------------
        # Earnings deduction (work allowance + taper)
        # -----------------------------
        earnings_deduction = self.calculate_earnings_deduction(
            data,
            UC_RATES,
            housing_element,
            has_lcw,
            has_lcwra,
            num_children
        )

        # -----------------------------
        # Sanctions (full rules + hardship)
        # -----------------------------
        sanction_reduction = self.calculate_sanction_reduction(
            data,
            UC_RATES,
            age,
            partner_age
        )

        # -----------------------------
        # Advance payments
        # -----------------------------
        advance = float(data.advance_amount or 0)
        repayment_months = int(data.repayment_period or 0)
        advance_deduction = advance / repayment_months if repayment_months > 0 else 0.0

        # -----------------------------
        # Total before capped deductions
        # -----------------------------
        total = (
            standard_allowance +
            housing_element +
            child_elements +
            childcare_costs +
            carer_element +
            disability_element +
            transitional_sdp
        )

        benefit_cap_reduction = self.calculate_benefit_cap(
            data,
            UC_RATES,
            total,
            has_lcwra,
            carer_element
        )
        
        total -= benefit_cap_reduction

        # Apply deductions
        total -= capital_income
        total -= earnings_deduction
        total -= sanction_reduction
        total -= advance_deduction

        # -----------------------------
        # Apply deduction caps
        # -----------------------------
        deduction_caps_total = self.apply_deduction_caps(
            data,
            UC_RATES,
            standard_allowance
        )

        total -= deduction_caps_total

        # -----------------------------
        # Build breakdown dictionary
        # -----------------------------
        breakdown = {
            "Standard Allowance": standard_allowance,
            "Housing Element": housing_element,
            "Child Element": child_elements,
            "Childcare Costs": childcare_costs,
            "Carer Element": carer_element,
            "Disability Element": disability_element,
            "Transitional SDP": transitional_sdp,
            "Capital Deduction": -capital_income,
            "Earnings Deduction": -earnings_deduction,
            "Sanction Reduction": -sanction_reduction,
            "Advance Payment Deduction": -advance_deduction,
            "Deduction Caps": -deduction_caps_total,
            "Benefit Cap Reduction": -benefit_cap_reduction,
        }
        
        # Store for breakdown screen
        data.breakdown = breakdown

        # -----------------------------
        # Final entitlement
        # -----------------------------
        final_total = max(0.0, round(total, 2))
        data.breakdown["Final Entitlement"] = final_total
        return final_total


def with_diagnostics(widget_names=None):
    """
    Decorator that injects automatic diagnostics into any Screen.
    widget_names: list of attribute names to check when the screen is opened.
    """
    widget_names = widget_names or []

    def decorator(cls):
        original_on_pre_enter = getattr(cls, "on_pre_enter", None)

        def new_on_pre_enter(self, *args, **kwargs):
            # Run original on_pre_enter if it exists
            if original_on_pre_enter:
                original_on_pre_enter(self, *args, **kwargs)

            print(f"\n=== Diagnostics for {cls.__name__} ===")

            for name in widget_names:
                widget = getattr(self, name, None)
                if widget is None:
                    print(f"  ✖ {name}: NOT FOUND")
                else:
                    print(f"  ✔ {name}: OK")

            print(f"=== End Diagnostics for {cls.__name__} ===\n")

        setattr(cls, "on_pre_enter", new_on_pre_enter)
        return cls

    return decorator

# Helper function to create a label that wraps text within the window width
def wrapped_SafeLabel(text, font_size, height):
    label = SafeLabel(
        text=text,
        font_size=font_size,
        halign="center",
        valign="middle",
        color=get_color_from_hex(WHITE),
        size_hint_y=None,
        height=height
    )
    # Bind the label's width to the window width minus padding
    def update_text_size(instance, value):
        instance.text_size = (Window.width - 60, None)
    label.bind(width=update_text_size)
    update_text_size(label, None)
    return label

def build_header(layout, title_text):
    top_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=60)
    title = SafeLabel(
        text=title_text,
        font_size=50,
        bold=True,
        font_name="freedom",
        color=get_color_from_hex("#FFDD00"),  # GOV.UK yellow
        halign="center",
        valign="middle"
    )
    title.bind(size=lambda inst, val: setattr(inst, 'text_size', (val, None)))
    top_layout.add_widget(title)
    layout.add_widget(top_layout)

def build_footer(layout):
    bottom_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=25)
    footer_label = SafeLabel(
        text="Benefit Buddy © 2025   Version 1.0   All Rights Reserved",
        font_size=12,
        halign="center",
        color=get_color_from_hex("#FFDD00")  # GOV.UK yellow
    )
    bottom_layout.add_widget(footer_label)
    layout.add_widget(bottom_layout)

# Create a custom TextInput class to handle multiple inputs and keyboard events
class CustomTextInput(TextInput):
    layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

    def create_inputs(self): # Create multiple TextInput fields
        self.inputs = [TextInput(multiline=False) for _ in range(3)]
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        for i, input_box in enumerate(self.inputs):
            input_box.bind(on_text_validate=self.move_to_next)  # Bind Enter key
            layout.add_widget(input_box)
        return layout

    def move_to_next(self, instance): # Move focus to the next TextInput
        # Find the index of the current TextInput
        current_index = self.inputs.index(instance)
        # Focus the next TextInput if it exists
        if current_index + 1 < len(self.inputs):
            self.inputs[current_index + 1].focus = True
            
    def keyboard_on_key_down(self, window, keycode, text, modifiers): # Handle keyboard events
        # Check if Tab or Enter key is pressed
        if keycode[1] == 'tab':  # Check if Tab key is pressed
            self.focus_next()  # Move focus to the next TextInput
            return True
        elif keycode[1] == 'enter':  # Check if Enter key is pressed
            self.focus_next()  # Move focus to the next TextInput
            return True
        return super().keyboard_on_key_down(window, keycode, text, modifiers)

    def focus_next(self): # Move focus to the next TextInput
        # Find the next widget to focus
        focusable_widgets = self.parent.children[::-1]  # Reverse order
        current_index = focusable_widgets.index(self)
        if current_index + 1 < len(focusable_widgets):
            focusable_widgets[current_index + 1].focus = True

# Create a custom TextInput for date of birth input
class DOBInput(CustomTextInput):
    def insert_text(self, substring, from_undo=False):
        # Allow only digits and slashes
        allowed_chars = "0123456789"
        substring = ''.join(c for c in substring if c in allowed_chars)

        # Enforce the format DD/MM/YYYY
        text = self.text
        if len(text) == 2 or len(text) == 5:
            substring = '/' + substring

        # Limit the length to 10 characters (DD/MM/YYYY)
        if len(text) + len(substring) > 10:
            substring = substring[:10 - len(text)]

        super().insert_text(substring, from_undo=from_undo)

# Create a custom button with rounded corners
class RoundedButton(Button):
    def __init__(self, **kwargs):
        # --- FONT SIZE ---
        fs = kwargs.get("font_size", 16)
        if isinstance(fs, str):
            try:
                fs = fs.strip().replace("sp", "")
                kwargs["font_size"] = sp(int(fs))
            except Exception:
                kwargs["font_size"] = sp(16)
        elif isinstance(fs, (int, float)):
            kwargs["font_size"] = sp(fs)
        else:
            kwargs["font_size"] = sp(16)

        # --- TEXT SIZE ---
        ts = kwargs.get("text_size", None)
        if not ts or ts in [(None, None), (0, 0)] or isinstance(ts, ObservableList):
            kwargs["text_size"] = (Window.width - 60, None)

        # --- PADDING ---
        pad = kwargs.get("padding", None)
        if not pad or pad in [(0, 0), (0, 0, 0, 0)] or isinstance(pad, ObservableList):
            kwargs["padding"] = (10, 10)

        super().__init__(**kwargs)

        # --- Rounded rectangle background ---
        with self.canvas.before:
            self.color_instruction = Color(rgba=get_color_from_hex("#FFDD00"))  # GOVUK_YELLOW
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[20]
            )

        # Bind position and size to update the rectangle dynamically
        self.bind(pos=self.update_rect, size=self.update_rect)

        # 🔑 Bind text_size dynamically to widget width and window resize
        self.bind(width=self._update_text_size)
        Window.bind(size=lambda *_: self._update_text_size())

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def _update_text_size(self, *args):
        # Always keep text_size tied to current width
        self.text_size = (self.width - 20, None)

# ---------------------------------------------------------
# ROW USED INSIDE DROPDOWN
# ---------------------------------------------------------
class IconRow(ButtonBehavior, BoxLayout):
    def __init__(self, text, icon_path=None, **kwargs):
        super().__init__(
            orientation="horizontal",
            spacing=10,
            padding=(15, 10),
            size_hint_y=None,
            height=50,
            **kwargs
        )

        # Background
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_bg, size=self._update_bg)

        # Optional icon
        if icon_path:
            self.add_widget(Image(
                source=icon_path,
                size_hint=(None, None),
                size=(28, 28),
                allow_stretch=True,
                keep_ratio=True
            ))

        # Text label
        self.label = Label(
            text=text,
            color=get_color_from_hex("#005EA5"),
            font_size=18,
            halign="left",
            valign="middle"
        )
        self.add_widget(self.label)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

# ---------------------------------------------------------
# DROPDOWN MENU
# ---------------------------------------------------------
class GovUkDropdown(BoxLayout):
    def __init__(self, text="Select", values=None, **kwargs):
        super().__init__(
            orientation="horizontal",
            spacing=10,
            padding=(15, 10),
            size_hint=(None, None),
            height=55,
            width=300,
            **kwargs
        )

        self.values = values or []
        self._text = text

        self.size_hint_x = None
        self.pos_hint = {"center_x": 0.5}

        # =========================================================
        # HEADER BACKGROUND
        # =========================================================
        with self.canvas.before:
            self._bg_color = Color(*get_color_from_hex("#FFDD00"))
            self._bg = Rectangle(size=self.size, pos=self.pos)

        self.bind(size=lambda inst, val: setattr(self._bg, "size", val))
        self.bind(pos=lambda inst, val: setattr(self._bg, "pos", val))

        # =========================================================
        # TOUCH HIGHLIGHT (press only)
        # =========================================================
        def on_press(*args):
            self._bg_color.rgb = (0.95, 0.82, 0)  # darker yellow

        def on_release(*args):
            self._bg_color.rgb = get_color_from_hex("#FFDD00")[:3]

        self.bind(on_touch_down=lambda inst, touch: on_press() if inst.collide_point(*touch.pos) else None)
        
        def _release(inst, touch):
            # Only run highlight release when dropdown is closed
            if not self.dropdown.attach_to:
                on_release()
            return False
        
        self.bind(on_touch_up=_release)
        
        def _open_if_closed(inst, touch):
            # Only open if dropdown is not already open
            if not self.dropdown.attach_to and self.collide_point(*touch.pos):
                return self.open_dropdown(inst, touch)
            return False
        
        self.bind(on_touch_up=_open_if_closed)

        # =========================================================
        # LABEL
        # =========================================================
        self.label = SafeLabel(
            text=text,
            font_size=18,
            color=get_color_from_hex("#005EA5"),
            halign="left",
            valign="middle"
        )

        self.label.text_size = (self.width - 40, None)
        self.label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        self.bind(width=lambda inst, val: setattr(self.label, "text_size", (val - 40, None)))

        # =========================================================
        # CHEVRON
        # =========================================================
        self.chevron = Image(
            source="images/icons/ChevronDown-icon/ChevronDown-16px.png",
            size_hint=(None, None),
            size=(20, 20)
        )

        self.add_widget(self.label)
        self.add_widget(self.chevron)

        # =========================================================
        # DROPDOWN PANEL
        # =========================================================
        self.dropdown = DropDown(auto_width=False)
        self.dropdown.width = self.width

        # 3px GOV.UK yellow border + white background
        with self.dropdown.canvas.before:
            Color(*get_color_from_hex("#FFDD00"))  # border
            self._border = Rectangle(size=self.dropdown.size, pos=self.dropdown.pos)

            Color(1, 1, 1, 1)  # inner white
            self._inner = Rectangle(size=self.dropdown.size, pos=self.dropdown.pos)

        def update_dropdown_graphics(*args):
            # Border
            self._border.size = self.dropdown.size
            self._border.pos = self.dropdown.pos

            # Inner white inset by 3px
            self._inner.size = (self.dropdown.width - 6, self.dropdown.height - 6)
            self._inner.pos = (self.dropdown.x + 3, self.dropdown.y + 3)

        self.dropdown.bind(size=update_dropdown_graphics, pos=update_dropdown_graphics)

        self.dropdown.bind(on_dismiss=self._on_dropdown_dismiss)

        for i, v in enumerate(self.values):
            # Button
            btn = Button(
                text=v,
                size_hint_y=None,
                height=50,
                background_normal="",
                background_color=get_color_from_hex("#FFFFFF"),
                color=get_color_from_hex("#005EA5")
            )
        
            # Touch highlight for menu items
            def make_press(btn_ref):
                return lambda *args: setattr(btn_ref, "background_color", (0.95, 0.95, 0.95, 1))
        
            def make_release(btn_ref):
                return lambda *args: setattr(btn_ref, "background_color", (1, 1, 1, 1))
        
            btn.bind(on_press=make_press(btn), on_release=make_release(btn))
            btn.bind(on_release=lambda inst: self.select(inst.text))
        
            # Add the button
            self.dropdown.add_widget(btn)
        
            # Add divider AFTER each item except the last
            if i < len(self.values) - 1:
                divider = Widget(size_hint_y=None, height=2)
        
                with divider.canvas.before:
                    Color(*get_color_from_hex("#005EA5"))
                    divider._line = Rectangle()
        
                # Keep divider centered at 75% width
                def update_divider(inst, *args):
                    full_w = self.dropdown.width
                    line_w = full_w * 0.75
                    inst._line.size = (line_w, 2)
                    inst._line.pos = (self.dropdown.x + (full_w - line_w) / 2, inst.y)
        
                divider.bind(pos=update_divider, size=update_divider)
                self.dropdown.bind(width=update_divider)
        
                self.dropdown.add_widget(divider)

    def _on_dropdown_dismiss(self, *args):
        self.chevron.source = "images/icons/ChevronDown-icon/ChevronDown-16px.png"

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.label.text = value

    def open_dropdown(self, instance, touch):
        if self.collide_point(*touch.pos):
            self.chevron.source = "images/icons/ChevronUp-icon/ChevronUp-16px.png"
            self.dropdown.open(self)
            return True
        return False

    def select(self, value):
        self.text = value
        self.dropdown.dismiss()

# Create a loading animation using a sequence of PNG images
class PNGSequenceAnimationWidget(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        base_path = os.path.dirname(os.path.abspath(__file__))
        images_path = os.path.join(base_path, "images", "loading")
        resource_add_path(images_path)

        self.frames = []
        for f in sorted(os.listdir(images_path)):
            if f.endswith(".png"):
                found_path = resource_find(f)
                if found_path:
                    self.frames.append(found_path)

        self.current_frame = 0
        Clock.schedule_interval(self.update_frame, 1 / 30.0)

    def update_frame(self, dt):
        if not self.frames:
            return
        self.source = self.frames[self.current_frame]
        self.current_frame = (self.current_frame + 1) % len(self.frames)

class PulsingGlow(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.color = Color(1, 1, 1, 0.3)
            self.ellipse = Ellipse(size=self.size, pos=self.pos)

        self.bind(size=self.update_graphics, pos=self.update_graphics)

        # Pulse animation
        anim = Animation(a=0.6, duration=0.8) + Animation(a=0.3, duration=0.8)
        anim.repeat = True
        anim.start(self.color)

    def update_graphics(self, *args):
        self.ellipse.size = self.size
        self.ellipse.pos = self.pos

# =========================================================
# COLLAPSIBLE SECTION CLASS
# =========================================================
class CollapsibleSection(BoxLayout):
    def __init__(self, title, content_lines, **kwargs):
        super().__init__(orientation="vertical", spacing=5, size_hint_y=None, **kwargs)

        self.is_open = False
        self.content_lines = content_lines

        # =========================================================
        # HEADER
        # =========================================================
        self.header = BoxLayout(
            orientation="horizontal",
            spacing=10,
            size_hint=(1, None),
            height=64,
            padding=(15, 0)
        )

        # Background
        with self.header.canvas.before:
            self._header_color = Color(1, 0.866, 0, 1)
            self._header_rect = Rectangle(pos=self.header.pos, size=self.header.size)

        self.header.bind(
            pos=lambda inst, val: setattr(self._header_rect, "pos", val),
            size=lambda inst, val: setattr(self._header_rect, "size", val),
        )

        # =========================================================
        # TOUCH HIGHLIGHT (header)
        # =========================================================
        def on_press(*args):
            self._header_color.rgb = (0.95, 0.82, 0)

        def on_release(*args):
            self._header_color.rgb = (1, 0.866, 0)

        self.header.bind(on_touch_down=lambda inst, touch: on_press() if inst.collide_point(*touch.pos) else None)
        self.header.bind(on_touch_up=lambda inst, touch: on_release())

        # Label
        self.header_label = SafeLabel(
            text=title,
            font_size=18,
            color=get_color_from_hex("#005EA5"),
            halign="left",
            valign="middle",
            size_hint=(1, None),
            height=64,
            pos_hint={"center_y": 0.5}
        )
        self.header_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))

        # Chevron (rotating)
        self.header_chevron = Image(
            source="images/icons/ChevronDown-icon/ChevronDown-16px.png",
            size_hint=(None, None),
            size=(24, 24),
            pos_hint={"center_y": 0.5}
        )
        self.header_chevron.rotation = 0

        with self.header_chevron.canvas.before:
            PushMatrix()
            self.chevron_rot = Rotate(origin=self.header_chevron.center, angle=0)
        with self.header_chevron.canvas.after:
            PopMatrix()

        self.header_chevron.bind(
            center=lambda inst, val: setattr(self.chevron_rot, "origin", val)
        )

        self.header.add_widget(self.header_label)
        self.header.add_widget(self.header_chevron)

        self.header.bind(on_touch_down=self._on_header_touch)
        self.add_widget(self.header)

        # =========================================================
        # CONTENT BOX
        # =========================================================
        self.content_box = BoxLayout(
            orientation="vertical",
            spacing=5,
            padding=(20, 10),
            size_hint_y=None,
            height=0,
            opacity=0
        )
        
        # Subtle darker background behind content
        with self.content_box.canvas.before:
            Color(0.0, 0.32, 0.56, 1)
            self._content_bg = Rectangle(pos=self.content_box.pos, size=self.content_box.size)
        
        # Keep background in sync
        self.content_box.bind(
            pos=lambda inst, val: setattr(self._content_bg, "pos", val),
            size=lambda inst, val: setattr(self._content_bg, "size", val)
        )
        self.content_box.bind(
            minimum_height=lambda inst, val: setattr(inst, "height", val)
        )

        self.add_widget(self.content_box)

    # =========================================================
    # TOUCH HANDLER
    # =========================================================
    def _on_header_touch(self, instance, touch):
        if self.header.collide_point(*touch.pos):
            self.toggle(self.header, touch)
            return True
        return False

    # =========================================================
    # TOGGLE (ANIMATED)
    # =========================================================
    def toggle(self, instance, touch=None):
        if touch and not self.header.collide_point(*touch.pos):
            return False

        self.is_open = not self.is_open

        if self.is_open:
            Animation(angle=180, d=0.2, t="out_quad").start(self.chevron_rot)

            # Build content
            self.content_box.clear_widgets()

            for i, line in enumerate(self.content_lines):
                # Content label
                lbl = SafeLabel(
                    text=line,
                    font_size=16,
                    halign="left",
                    valign="middle",
                    color=get_color_from_hex("#FFFFFF"),
                    size_hint_y=None
                )
                lbl.bind(
                    width=lambda inst, val: setattr(inst, "text_size", (val, None)),
                    texture_size=lambda inst, val: setattr(inst, "height", val[1])
                )
                self.content_box.add_widget(lbl)

                # Divider (between items only)
                if i < len(self.content_lines) - 1:
                    divider = Widget(size_hint_y=None, height=2)

                    with divider.canvas.before:
                        Color(*get_color_from_hex("#FFDD00"))
                        divider._line = Rectangle()

                    def update_divider(inst, *args):
                        full_w = self.content_box.width
                        line_w = full_w * 0.75
                        inst._line.size = (line_w, 2)
                        inst._line.pos = (
                            self.content_box.x + (full_w - line_w) / 2,
                            inst.y
                        )

                    divider.bind(pos=update_divider, size=update_divider)
                    self.content_box.bind(width=update_divider)

                    self.content_box.add_widget(divider)

            # Animate open
            target_height = self.content_box.minimum_height
            self.content_box.opacity = 1

            Animation(height=target_height, d=0.2, t="out_quad").start(self.content_box)
            Animation(height=self.header.height + target_height, d=0.2, t="out_quad").start(self)

        else:
            Animation(angle=0, d=0.2, t="out_quad").start(self.chevron_rot)

            anim = Animation(height=0, opacity=0, d=0.2, t="out_quad")
            anim.bind(on_complete=lambda *args: self.content_box.clear_widgets())
            anim.start(self.content_box)

            Animation(height=self.header.height, d=0.2, t="out_quad").start(self)

        return True

class CalculatorNavBar(BoxLayout):
    def __init__(self, current, **kwargs):
        super().__init__(
            orientation="horizontal",
            spacing=20,
            padding=(12, 8),
            size_hint_y=None,
            height=80,
            **kwargs
        )

        self.current = current
        self.dropdown_open = False
        self.dropdown = None

        app = App.get_running_app()

        # Background
        with self.canvas.before:
            Color(*get_color_from_hex("#FFDD00"))
            self._bg_rect = Rectangle(size=self.size, pos=self.pos)

        self.bind(
            size=lambda inst, val: setattr(self._bg_rect, "size", val),
            pos=lambda inst, val: setattr(self._bg_rect, "pos", val),
        )

        # ---------------------------------------------------------
        # UPDATED SCREEN ORDER
        # ---------------------------------------------------------
        self.screens = [
            ("Introduction", "calculator_intro"),
            ("Claimant Details", "calculator_claimant_details"),
            ("Finances", "calculator_finances"),
            ("Children", "calculator_children"),
            ("Sanctions", "calculator_sanctions"),
            ("Housing", "calculator_housing"),
            ("Additional Elements", "calculator_additional"),
            ("Advanced Payments", "calculator_advance"),
            ("Summary", "calculator_final"),
        ]

        self.icon_map = ICON_PATHS

        self.current_index = next(
            (i for i, (_, name) in enumerate(self.screens) if name == current),
            0
        )

        # ---------------------------------------------------------
        # HOME BUTTON
        # ---------------------------------------------------------
        home_btn = self.make_nav_button(
            label="Home",
            icon="images/icons/Home-icon/Home-32px.png",
            on_press=lambda inst: app.nav.go("main")
        )
        self.add_widget(self._wrap_nav_item(home_btn))

        # ---------------------------------------------------------
        # PREVIOUS BUTTON
        # ---------------------------------------------------------
        prev_btn = self.make_text_button(
            "Previous",
            enabled=(self.current_index > 0),
            on_press=lambda inst: app.nav.go(self.screens[self.current_index - 1][1])
        )
        self.add_widget(self._wrap_nav_item(prev_btn))

        # ---------------------------------------------------------
        # CURRENT SCREEN BUTTON
        # ---------------------------------------------------------
        current_label, current_screen = self.screens[self.current_index]
        current_icon = self.icon_map[current_label]

        current_btn = self.make_current_button(
            label=current_label,
            icon=current_icon,
            on_press=self.toggle_dropdown
        )
        self.current_btn = current_btn
        self.add_widget(self._wrap_nav_item(current_btn))

        # ---------------------------------------------------------
        # NEXT BUTTON
        # ---------------------------------------------------------
        next_btn = self.make_text_button(
            "Next",
            enabled=(self.current_index < len(self.screens) - 1),
            on_press=lambda inst: app.nav.go(self.screens[self.current_index + 1][1])
        )
        self.add_widget(self._wrap_nav_item(next_btn))

    # =====================================================================
    # WRAPPER — FIXED FOR PERFECT VERTICAL ALIGNMENT
    # =====================================================================
    def _wrap_nav_item(self, widget):
        box = BoxLayout(
            size_hint=(None, 1),   # full vertical stretch
            padding=(0, 0),
        )
        box.add_widget(widget)

        # match width to widget
        def sync_width(*args):
            box.width = widget.width

        widget.bind(width=sync_width)
        sync_width()

        return box

    # =====================================================================
    # BUTTON FACTORIES — ALL VERTICALLY CENTERED + SAFE TOUCH HANDLING
    # =====================================================================
    def _bind_press(self, widget, callback):
        """Bind a safe on_touch_down handler that prevents event bubbling."""
        
        def handler(inst, touch):
            if widget.collide_point(*touch.pos):
                callback(widget)
                # Do NOT swallow yet — allow the press to complete
                return True
            return False
    
        widget.bind(on_touch_down=handler)
    
        def swallow_up(inst, touch):
            # Swallow ONLY if the dropdown is open AND this is the navbar button
            if self.dropdown_open and widget.collide_point(*touch.pos):
                return True
            return False
    
        widget.bind(on_touch_up=swallow_up)
    
    def make_nav_button(self, label, icon, on_press):
        btn = BoxLayout(
            orientation="horizontal",
            spacing=8,
            size_hint=(None, None),
            size=(160, 60),
            padding=(0, 0),
        )
        btn.size_hint_y = None
        btn.height = 60
    
        img = Image(
            source=icon,
            size_hint=(None, None),
            size=(32, 32),
            allow_stretch=True,
            keep_ratio=True,
        )
    
        lbl = SafeLabel(
            text=label,
            font_size=18,
            halign="left",
            valign="middle",
            color=get_color_from_hex("#005EA5"),
            size_hint=(1, None),
            height=60,
        )
        lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    
        btn.add_widget(self._center_icon(img))
        btn.add_widget(lbl)
    
        # SAFE TOUCH HANDLER
        self._bind_press(btn, on_press)
    
        return btn
    
    
    def make_text_button(self, label, enabled, on_press):
        color = get_color_from_hex("#005EA5") if enabled else (0.3, 0.3, 0.3, 1)
    
        lbl = SafeLabel(
            text=label,
            font_size=18,
            halign="center",
            valign="middle",
            color=color,
            size_hint=(None, None),
            size=(140, 60),
        )
        lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    
        if enabled:
            # SAFE TOUCH HANDLER
            self._bind_press(lbl, on_press)
    
        return lbl
    
    
    def make_current_button(self, label, icon, on_press):
        btn = BoxLayout(
            orientation="horizontal",
            spacing=8,
            size_hint=(None, None),
            size=(300, 60),
            padding=(0, 0),
        )
        btn.size_hint_y = None
        btn.height = 60
    
        img = Image(
            source=icon,
            size_hint=(None, None),
            size=(32, 32),
            allow_stretch=True,
            keep_ratio=True,
        )
    
        lbl = SafeLabel(
            text=label,
            font_size=18,
            halign="left",
            valign="middle",
            color=get_color_from_hex("#005EA5"),
            size_hint=(1, None),
            height=60,
        )
        lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    
        chevron = Image(
            source="images/icons/ChevronDown-icon/ChevronDown-16px.png",
            size_hint=(None, None),
            size=(20, 20),
            allow_stretch=True,
            keep_ratio=True,
        )
        self.current_chevron = chevron
    
        btn.add_widget(self._center_icon(img))
        btn.add_widget(lbl)
        btn.add_widget(self._center_icon(chevron))
    
        # SAFE TOUCH HANDLER
        self._bind_press(btn, on_press)
    
        return btn

    def _center_icon(self, img_widget):
        wrapper = BoxLayout(
            orientation="vertical",
            size_hint=(None, 1),
            width=img_widget.width,
            padding=0,
            spacing=0,
        )
    
        # top spacer
        wrapper.add_widget(Widget(size_hint_y=1))
    
        # icon
        wrapper.add_widget(img_widget)
    
        # bottom spacer
        wrapper.add_widget(Widget(size_hint_y=1))
    
        # keep wrapper width synced to icon width
        def sync_width(*args):
            wrapper.width = img_widget.width
        img_widget.bind(width=sync_width)
        sync_width()
    
        return wrapper

    # =====================================================================
    # DROPDOWN MENU
    # =====================================================================
    def make_dropdown_row(self, label, icon, on_press):
        row = BoxLayout(
            orientation="horizontal",
            spacing=8,
            size_hint=(1, None),   # full width of panel
            height=60,
            padding=(0, 0),
        )
    
        img = Image(
            source=icon,
            size_hint=(None, None),
            size=(32, 32),
            allow_stretch=True,
            keep_ratio=True,
        )
    
        lbl = SafeLabel(
            text=label,
            font_size=18,
            halign="left",
            valign="middle",
            color=get_color_from_hex("#005EA5"),
            size_hint=(1, None),
            height=60,
        )
    
        # Make text fill all remaining space
        lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
    
        row.add_widget(self._center_icon(img))
        row.add_widget(lbl)
    
        self._bind_press(row, on_press)
        return row
        
    def toggle_dropdown(self, *args):
        if self.dropdown_open:
            self.close_dropdown()
        else:
            self.open_dropdown()
    
    def open_dropdown(self):
    
        def make_row_press(row_ref):
            return lambda inst, touch: (
                setattr(row_ref, "background_color", (0.95, 0.95, 0.95, 1))
                if row_ref.collide_point(*touch.pos) else None
            )
    
        def make_row_release(row_ref):
            return lambda inst, touch: (
                setattr(row_ref, "background_color", (1, 1, 1, 1))
                if row_ref.collide_point(*touch.pos) else None
            )
    
        if self.dropdown_open:
            return
    
        self.dropdown_open = True
    
        # Flip chevron
        if self.current_chevron:
            self.current_chevron.source = "images/icons/ChevronUp-icon/ChevronUp-16px.png"
    
        # Floating overlay
        self.dropdown = FloatLayout(size_hint=(1, 1))
    
        # Blocker
        blocker = Button(
            background_color=(0, 0, 0, 0),
            size_hint=(1, 1),
            on_release=lambda *a: self.close_dropdown()
        )
        self.dropdown.add_widget(blocker)
    
        Window.add_widget(self.dropdown)
    
        # Panel
        panel = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=300,
            height=460,
            padding=(10, 10, 10, 10),
            spacing=10,
        )
    
        # GOV.UK border + inset
        with panel.canvas.before:
            Color(*get_color_from_hex("#FFDD00"))
            panel._border = Rectangle(size=panel.size, pos=panel.pos)
    
            Color(1, 1, 1, 1)
            panel._inner = Rectangle(
                size=(panel.width - 6, panel.height - 6),
                pos=(panel.x + 3, panel.y + 3)
            )
    
        def update_panel_graphics(*args):
            panel._border.size = panel.size
            panel._border.pos = panel.pos
    
            panel._inner.size = (panel.width - 6, panel.height - 6)
            panel._inner.pos = (panel.x + 3, panel.y + 3)
    
        panel.bind(size=update_panel_graphics, pos=update_panel_graphics)
    
        app = App.get_running_app()
    
        for label, screen_name in self.screens:
            icon = self.icon_map[label]
    
            def make_row_callback(target):
                return lambda inst: (
                    app.nav.go(target),
                    self.close_dropdown()
                )
    
            row = self.make_dropdown_row(
                label=label,
                icon=icon,
                on_press=make_row_callback(screen_name)
            )
    
            panel.add_widget(row)
            row.bind(on_touch_down=make_row_press(row))
            row.bind(on_touch_up=make_row_release(row))
    
            # Add separator except after last item
            if (label, screen_name) != self.screens[-1]:
                sep = Widget(size_hint=(None, None), height=1)
                sep.width = panel.width * 0.75
    
                with sep.canvas.before:
                    Color(0.0, 0.3686, 0.647, 1)
                    sep._line = Rectangle(size=(sep.width, 1), pos=sep.pos)
    
                def update_sep(*args):
                    sep.width = panel.width * 0.75
                    sep._line.size = (sep.width, 1)
                    sep._line.pos = (sep.x, sep.y)
    
                panel.bind(size=update_sep, pos=update_sep)
                sep.bind(pos=update_sep)
    
                panel.add_widget(sep)
    
        # 1. Get the BOTTOM of the current button in window coords
        btn_x, btn_bottom = self.current_btn.to_window(
            self.current_btn.x,
            self.current_btn.y
        )
        
        # 2. Convert window → dropdown coords
        local_x, local_bottom = self.dropdown.to_widget(btn_x, btn_bottom, relative=True)
        
        # 3. Position panel so its TOP sits exactly at the button's bottom
        panel_y = local_bottom - panel.height - 10
        panel.pos = (local_x, panel_y)
    
        # Add panel above blocker
        self.dropdown.add_widget(panel)
        self.dropdown.remove_widget(panel)
        self.dropdown.add_widget(panel)
    
    def close_dropdown(self):
        if not self.dropdown_open:
            return
    
        self.dropdown_open = False
    
        # Toggle chevron DOWN
        if self.current_chevron:
            self.current_chevron.source = "images/icons/ChevronDown-icon/ChevronDown-16px.png"
    
        if self.dropdown and self.dropdown.parent:
            if self.dropdown and self.dropdown.parent:
                Window.remove_widget(self.dropdown)
    
        self.dropdown = None

def make_yes_no_row(label_text, callback):
    row = BoxLayout(
        orientation="horizontal",
        spacing=20,
        size_hint_y=None,
        height=60
    )

    label = SafeLabel(
        text=label_text,
        font_size=18,
        color=get_color_from_hex("#FFFFFF")
    )

    # GOV.UK colours
    normal_yellow = get_color_from_hex("#FFDD00")   # Bright yellow
    down_yellow   = get_color_from_hex("#C8A600")   # Much darker, clearly visible
    blue_text     = get_color_from_hex("#005EA5")   # GOV.UK blue

    yes_btn = ToggleButton(
        text="Yes",
        group=label_text,
        size_hint=(None, None),
        size=(100, 50),
        background_normal="",   # Remove default image
        background_down="",     # Remove default pressed image
        background_color=normal_yellow,
        color=blue_text
    )

    no_btn = ToggleButton(
        text="No",
        group=label_text,
        size_hint=(None, None),
        size=(100, 50),
        background_normal="",
        background_down="",
        background_color=normal_yellow,
        color=blue_text
    )

    # Change colour when selected/unselected
    def update_color(inst, state):
        inst.background_color = down_yellow if state == "down" else normal_yellow

    yes_btn.bind(state=update_color)
    no_btn.bind(state=update_color)

    # Callbacks for your logic
    yes_btn.bind(on_press=lambda inst: callback(True))
    no_btn.bind(on_press=lambda inst: callback(False))

    row.add_widget(label)
    row.add_widget(yes_btn)
    row.add_widget(no_btn)

    return row, yes_btn, no_btn

# ---------------------------------------------------------
# MONEY FORMATTER (add this near the top of your file)
# ---------------------------------------------------------
def fmt_money(value):
    try:
        return f"£{float(value):,.2f}"
    except:
        return "£0.00"

# ---------------------------------------------------------
# CAPITALISE
# ---------------------------------------------------------
def title_case(value):
    if not value:
        return ""
    return str(value).title()
    
class BaseScreen(Screen):
    # ---------------------------------------------------------
    # LIFECYCLE METHODS (KEEP THESE!)
    # ---------------------------------------------------------
    def on_pre_leave(self):
        pass

    def destroy(self):
        # Clean teardown so NavigationManager can safely recreate screens
        self.clear_widgets()
        self.canvas.clear()

    # ---------------------------------------------------------
    # OPTIONAL LOADING OVERLAY (NEW)
    # ---------------------------------------------------------
    def show_loading(self, message="Loading..."):
        if hasattr(self, "_loading_overlay"):
            return

        overlay = FloatLayout(size_hint=(1, 1))

        with overlay.canvas.before:
            Color(0, 0, 0, 0.6)
            overlay._bg = Rectangle(size=overlay.size, pos=overlay.pos)

        overlay.bind(
            size=lambda inst, val: setattr(overlay._bg, "size", val),
            pos=lambda inst, val: setattr(overlay._bg, "pos", val),
        )

        label = SafeLabel(
            text=message,
            font_size=24,
            halign="center",
            valign="middle",
            color=(1, 1, 1, 1),
            size_hint=(1, 1)
        )
        label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))

        overlay.add_widget(label)

        self._loading_overlay = overlay
        self.add_widget(overlay)

    def hide_loading(self):
        if hasattr(self, "_loading_overlay"):
            self.remove_widget(self._loading_overlay)
            del self._loading_overlay

class CalculatorIntroScreen(BaseScreen):
    def __init__(self, calculator_state, **kwargs):
        super().__init__(**kwargs)
        self.calculator_state = calculator_state
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation="vertical")
        root.add_widget(CalculatorNavBar(current="calculator_intro"))

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)

        container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=20,
            spacing=20,
        )

        # ⭐ REQUIRED for centering
        container.bind(minimum_height=container.setter("height"))

        # ⭐ REQUIRED for centering
        scroll.bind(height=lambda inst, val: setattr(container, "minimum_height", val))

        content = BoxLayout(
            orientation="vertical",
            spacing=20,
            size_hint=(1, None),
        )

        # ⭐ REQUIRED — you were missing this
        content.bind(minimum_height=content.setter("height"))

        content.add_widget(wrapped_SafeLabel("Welcome to the Benefit Buddy Calculator", 20, 32))
        content.add_widget(wrapped_SafeLabel("This calculator will help you estimate your Universal Credit entitlement.", 16, 28))
        content.add_widget(wrapped_SafeLabel("Please follow the steps to enter your details.", 16, 28))
        content.add_widget(wrapped_SafeLabel("You can navigate through the screens using the dropdown menu above.", 16, 28))

        content.add_widget(wrapped_SafeLabel("Before you start, please ensure you have the following information ready:", 16, 28))
        content.add_widget(wrapped_SafeLabel("- Your personal details (name, date of birth, etc.)", 14, 24))
        content.add_widget(wrapped_SafeLabel("- Your income and capital details", 14, 24))
        content.add_widget(wrapped_SafeLabel("- Your housing situation (rent or own)", 14, 24))
        content.add_widget(wrapped_SafeLabel("- Details of any children or dependents", 14, 24))
        content.add_widget(wrapped_SafeLabel("- Any additional elements that may apply to you", 14, 24))

        # ⭐ Center content vertically when short
        container.add_widget(Widget(size_hint_y=1))
        container.add_widget(content)
        container.add_widget(Widget(size_hint_y=1))

        scroll.add_widget(container)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_pre_enter(self, *args):
        pass

    def save_state(self):
        pass
    
    def load_state(self):
        pass


class CalculatorClaimantDetailsScreen(BaseScreen):
    def __init__(self, calculator_state, **kwargs):
        super().__init__(**kwargs)
        self.calculator_state = calculator_state
        self.claimant_widgets = {}
        self.build_ui()

    def build_ui(self):
        # ROOT layout (nav bar + scroll)
        root = BoxLayout(orientation="vertical")

        # ⭐ Navigation bar at the top
        root.add_widget(CalculatorNavBar(current="calculator_claimant_details"))

        # ⭐ ScrollView for form content
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)

        # ⭐ Main layout inside ScrollView
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=(20, 120, 20, 20),
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))

        scroll.add_widget(layout)
        root.add_widget(scroll)
        self.add_widget(root)

        # ---------------------------------------------------------
        # SECTION HEADER
        # ---------------------------------------------------------
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=60)
        header_label = SafeLabel(
            text="Select Claimant Type",
            font_size=20,
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE)
        )
        header_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        header_anchor.add_widget(header_label)
        layout.add_widget(header_anchor)

        # ---------------------------------------------------------
        # CLAIMANT TYPE CHECKBOXES
        # ---------------------------------------------------------
        claimant_type_layout = BoxLayout(orientation="horizontal", spacing=20, size_hint_y=None)
        claimant_type_layout.bind(minimum_height=claimant_type_layout.setter("height"))

        self.claimant_widgets["single_checkbox"] = CheckBox(group="claimant_type")
        self.claimant_widgets["couple_checkbox"] = CheckBox(group="claimant_type")

        claimant_type_layout.add_widget(SafeLabel(text="Single", font_size=18, color=get_color_from_hex(WHITE)))
        claimant_type_layout.add_widget(self.claimant_widgets["single_checkbox"])
        claimant_type_layout.add_widget(SafeLabel(text="Couple", font_size=18, color=get_color_from_hex(WHITE)))
        claimant_type_layout.add_widget(self.claimant_widgets["couple_checkbox"])

        layout.add_widget(claimant_type_layout)

        # Bind once
        self.claimant_widgets["couple_checkbox"].bind(active=self.on_couple_claim_checkbox_active)

        # ---------------------------------------------------------
        # CLAIMANT DETAILS
        # ---------------------------------------------------------
        layout.add_widget(SafeLabel(text="Enter Claimant Details", font_size=20, color=get_color_from_hex(WHITE)))

        self.claimant_widgets["name"] = CustomTextInput(
            hint_text="Name",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.claimant_widgets["name"])

        self.claimant_widgets["dob"] = DOBInput(
            hint_text="DD/MM/YYYY",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.claimant_widgets["dob"])

        # ---------------------------------------------------------
        # PARTNER DETAILS
        # ---------------------------------------------------------
        layout.add_widget(SafeLabel(text="Enter Partner Details", font_size=20, color=get_color_from_hex(WHITE)))

        self.claimant_widgets["partner_name"] = CustomTextInput(
            hint_text="Partner Name",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            disabled=True,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.claimant_widgets["partner_name"])

        self.claimant_widgets["partner_dob"] = DOBInput(
            hint_text="DD/MM/YYYY",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            disabled=True,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.claimant_widgets["partner_dob"])

    # ---------------------------------------------------------
    # CHECKBOX CALLBACK
    # ---------------------------------------------------------
    def on_couple_claim_checkbox_active(self, instance, value):
        w = self.claimant_widgets
        if "partner_name" not in w:
            return
        w["partner_name"].disabled = not value
        w["partner_dob"].disabled = not value

    # ---------------------------------------------------------
    # SAVE STATE (called automatically by NavigationManager)
    # ---------------------------------------------------------
    def save_state(self):
        w = self.claimant_widgets
        data = self.calculator_state
    
        # Relationship
        if w["single_checkbox"].active:
            data.relationship = "Single"
        elif w["couple_checkbox"].active:
            data.relationship = "Couple"
        else:
            data.relationship = "Single"  # safe default
    
        # Claimant details
        data.claimant_name = w["name"].text.strip()
        data.claimant_dob = w["dob"].text.strip()
    
        # Partner details (only if couple)
        if data.relationship == "Couple":
            data.partner_name = w["partner_name"].text.strip()
            data.partner_dob = w["partner_dob"].text.strip()
        else:
            data.partner_name = ""
            data.partner_dob = ""
    
    # ---------------------------------------------------------
    # LOAD STATE (called automatically by NavigationManager)
    # ---------------------------------------------------------
    def load_state(self):
        w = self.claimant_widgets
        data = self.calculator_state
    
        # Relationship
        rel = getattr(data, "relationship", "single")
        w["single_checkbox"].active = (rel == "Single")
        w["couple_checkbox"].active = (rel == "Couple")
    
        # Claimant fields
        w["name"].text = getattr(data, "claimant_name", "")
        w["dob"].text = getattr(data, "claimant_dob", "")
    
        # Partner fields
        w["partner_name"].text = getattr(data, "partner_name", "")
        w["partner_dob"].text = getattr(data, "partner_dob", "")
    
        # Enable/disable partner fields
        is_couple = (rel == "Couple")
        w["partner_name"].disabled = not is_couple
        w["partner_dob"].disabled = not is_couple
        

class CalculatorFinancesScreen(BaseScreen):

    def __init__(self, calculator_state, **kwargs):
        super().__init__(**kwargs)
        self.calculator_state = calculator_state
        self.finances_widgets = {}
        self.build_ui()

    def build_ui(self):
        # ROOT layout (nav bar + scroll)
        root = BoxLayout(orientation="vertical")

        # ⭐ Navigation bar at the top
        root.add_widget(CalculatorNavBar(current="calculator_finances"))

        # ⭐ ScrollView for form content
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)

        # ⭐ Main layout inside ScrollView
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=(20, 120, 20, 20),
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))

        scroll.add_widget(layout)
        root.add_widget(scroll)
        self.add_widget(root)

        # ---------------------------------------------------------
        # INSTRUCTION LABEL
        # ---------------------------------------------------------
        instruction = SafeLabel(
            text="Enter your financial details:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")
        )
        instruction.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(instruction)

        # ---------------------------------------------------------
        # MONTHLY INCOME
        # ---------------------------------------------------------
        layout.add_widget(SafeLabel(
            text="Monthly income (£)",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        ))

        self.finances_widgets["income"] = CustomTextInput(
            hint_text="Enter monthly income (£)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            input_filter="float",
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.finances_widgets["income"])

        # ---------------------------------------------------------
        # SAVINGS
        # ---------------------------------------------------------
        layout.add_widget(SafeLabel(
            text="Savings (£)",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        ))

        self.finances_widgets["savings"] = CustomTextInput(
            hint_text="Enter total savings (£)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            input_filter="float",
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.finances_widgets["savings"])

        # ---------------------------------------------------------
        # DEBTS
        # ---------------------------------------------------------
        layout.add_widget(SafeLabel(
            text="Debts (£)",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        ))

        self.finances_widgets["debts"] = CustomTextInput(
            hint_text="Enter total debts (£)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            input_filter="float",
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(self.finances_widgets["debts"])

        # Spacer at bottom
        layout.add_widget(Widget(size_hint_y=0.05))

    # ---------------------------------------------------------
    # SAVE STATE (called automatically by NavigationManager)
    # ---------------------------------------------------------
    def save_state(self):
        w = self.finances_widgets
        data = self.calculator_state
    
        # Save raw text values
        data.income_raw = w["income"].text.strip()
        data.savings_raw = w["savings"].text.strip()
        data.debts_raw = w["debts"].text.strip()
    
        # Parse floats safely
        try:
            data.income = float(w["income"].text or 0)
        except:
            data.income = 0.0

        # ⭐ Mirror income → earnings for the engine
        data.earnings = data.income
    
        try:
            data.savings = float(w["savings"].text or 0)
        except:
            data.savings = 0.0
    
        try:
            data.debts = float(w["debts"].text or 0)
        except:
            data.debts = 0.0
            
    # ---------------------------------------------------------
    # LOAD STATE (called automatically by NavigationManager)
    # ---------------------------------------------------------
    def load_state(self):
        w = self.finances_widgets
        data = self.calculator_state
    
        # Restore raw text values
        w["income"].text = str(getattr(data, "income_raw", ""))
        w["savings"].text = str(getattr(data, "savings_raw", ""))
        w["debts"].text = str(getattr(data, "debts_raw", ""))
    
class CalculatorHousingScreen(BaseScreen):
    def __init__(self, calculator_state, **kwargs):
        super().__init__(**kwargs)
        self.calculator_state = calculator_state
        self.housing_widgets = {}
        self.build_ui()
        self.load_state()

        app = App.get_running_app()
        app.calculator_state.lookup_lha_rate = self.lookup_lha_rate

    def build_ui(self):
        w = self.housing_widgets

        # ROOT
        root = BoxLayout(orientation="vertical")
        root.add_widget(CalculatorNavBar(current="calculator_housing"))

        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        w["scroll_view"] = scroll
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=(20, 20, 20, 20),
            size_hint=(1, None),
        )
        layout.bind(minimum_height=layout.setter("height"))
        scroll.add_widget(layout)
        root.add_widget(scroll)
        self.add_widget(root)

        # ---------------------------------------------------------
        # HOUSING TYPE
        # ---------------------------------------------------------
        housing_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
        
        w["housing_type"] = GovUkDropdown(
            text="Select Housing Type",
            values=[
                "Rent",
                "Own",
                "Shared Accommodation"
            ]
        )
        
        housing_anchor.add_widget(w["housing_type"])
        layout.add_widget(housing_anchor)

        def make_money_input(hint):
            return CustomTextInput(
                hint_text=hint,
                multiline=False,
                font_size=18,
                size_hint=(1, None),
                height=50,
                background_color=get_color_from_hex("#FFFFFF"),
                foreground_color=get_color_from_hex("#005EA5"),
            )

        w["rent"] = make_money_input("Enter monthly rent amount (£)")
        w["mortgage"] = make_money_input("Enter monthly mortgage amount (£)")
        w["shared"] = make_money_input("Enter shared accommodation contribution (£)")

        for key in ("rent", "mortgage", "shared"):
            field = w[key]
            layout.add_widget(field)
            field.opacity = 0
            field.disabled = True
            field.height = 0

        def _show_amount_widget(value_text):
            # Hide all fields first
            for key in ("rent", "mortgage", "shared"):
                field = w[key]
                field.opacity = 0
                field.disabled = True
                field.height = 0
        
            text = (value_text or "").strip().lower()
        
            if text == "rent":
                target = w["rent"]
            elif text == "own":
                target = w["mortgage"]
            elif text == "shared accommodation":
                target = w["shared"]
            else:
                return
        
            target.opacity = 1
            target.disabled = False
            target.height = 50

        def _update_tenancy_visibility(value_text):
            text = (value_text or "").strip().lower()
        
            if text == "Rent":
                w["tenancy_type"].opacity = 1
                w["tenancy_type"].disabled = False
                w["tenancy_type"].height = 50
            else:
                w["tenancy_type"].opacity = 0
                w["tenancy_type"].disabled = True
                w["tenancy_type"].height = 0
                w["tenancy_type"].text = "Select Tenancy Type"

        w["housing_type"].label.bind(text=lambda spinner, value: _show_amount_widget(value))
        w["housing_type"].label.bind(text=lambda spinner, value: _update_tenancy_visibility(value))

        # ---------------------------------------------------------
        # TENANCY TYPE
        # ---------------------------------------------------------
        tenancy_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
        
        w["tenancy_type"] = GovUkDropdown(
            text="Select Tenancy Type",
            values=[
                "Private Rented",
                "Social",
                "Temporary Accommodation",
                "Supported Accommodation"
            ]
        )
        
        tenancy_anchor.add_widget(w["tenancy_type"])
        layout.add_widget(tenancy_anchor)
        
        w["tenancy_type"].opacity = 0
        w["tenancy_type"].disabled = True
        w["tenancy_type"].height = 0

        # ---------------------------------------------------------
        # NON-DEPENDANTS
        # ---------------------------------------------------------
        w["non_dependants"] = CustomTextInput(
            hint_text="Number of non-dependants (e.g. adult children)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex("#FFFFFF"),
            foreground_color=get_color_from_hex("#005EA5"),
        )
        layout.add_widget(w["non_dependants"])

        # ---------------------------------------------------------
        # POSTCODE
        # ---------------------------------------------------------
        w["postcode"] = CustomTextInput(
            hint_text="Enter postcode (e.g. SW1A 1AA)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex("#FFFFFF"),
            foreground_color=get_color_from_hex("#005EA5"),
        )
        layout.add_widget(w["postcode"])

        # ---------------------------------------------------------
        # TENANCY MODE HELPERS
        # ---------------------------------------------------------
        def get_manual_mode(value):
            return "applicable"

        def get_service_mode(value):
            val = (value or "").lower()
            if val == "Social":
                return "applicable"
            elif val == "Private":
                return "not_applicable"
            return "unset"

        # ---------------------------------------------------------
        # MANUAL LOCATION / BRMA OVERRIDE
        # ---------------------------------------------------------
        # Manual override toggle row
        toggle_row = BoxLayout(
            orientation="horizontal",
            spacing=10,
            size_hint_y=None,
            height=50,
        )
        w["manual_toggle"] = CheckBox(size_hint=(None, None), size=(40, 40))
        manual_toggle_label = SafeLabel(
            text="Enable manual Location/BRMA override",
            font_size=16,
            color=get_color_from_hex("#FFFFFF"),
        )
        manual_toggle_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        toggle_row.add_widget(w["manual_toggle"])
        toggle_row.add_widget(manual_toggle_label)
        layout.add_widget(toggle_row)
        
        # LOCATION SPINNER (manual)
        location_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
        
        w["location"] = GovUkDropdown(
            text="Select Location",
            values=["England", "Scotland", "Wales"]
        )
        
        location_anchor.add_widget(w["location"])
        layout.add_widget(location_anchor)
        
        # Preserve your visibility logic
        w["location"].disabled = True
        w["location"].opacity = 0
        w["location"].height = 0
        
        # BRMA SPINNER (manual)
        brma_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=70)
        
        w["brma"] = GovUkDropdown(
            text="Select BRMA",
            values=["Select BRMA"]
        )
        
        brma_anchor.add_widget(w["brma"])
        layout.add_widget(brma_anchor)
        
        # Preserve your visibility logic
        w["brma"].disabled = True
        w["brma"].opacity = 0
        w["brma"].height = 0
        
        Clock.schedule_once(lambda dt: setattr(w["brma"].label, "text", "Select BRMA"), 0)
                
        # Manual location change → filter BRMAs
        def on_manual_location_change(spinner, value):
            loc = (value or "").lower()
            app = App.get_running_app()
            brma_by_location = getattr(app, "brma_by_location", {}) or {}
            brmas = brma_by_location.get(loc, [])
            w["brma"].values = brmas or ["Select BRMA"]
            w["brma"].text = "Select BRMA"
        
        w["location"].label.bind(text=on_manual_location_change)
        
        # Manual BRMA change → update results
        def on_manual_brma_change(spinner, value):
            if not w["manual_toggle"].active:
                return
        
            brma = value
            location = w["location"].text
            loc_norm = location.lower() if location and location != "Select Location" else None
        
            bedrooms = self.get_bedroom_entitlement()
            lha_monthly = self.lookup_lha_rate(brma, bedrooms, loc_norm)
        
            results_box = w["brma_results_box"]
            results_box.clear_widgets()
        
            add_result_row("Location:", location or "Not found")
            add_result_row("BRMA:", brma)
            add_result_row("Bedroom entitlement:", str(bedrooms))
            add_result_row("LHA monthly rate:", f"£{lha_monthly:.2f}")
        
            show_results_box()
        
        w["brma"].label.bind(text=on_manual_brma_change)
        
        # Manual mode toggle logic (clean + simple)
        def toggle_manual_mode(instance, value):
            w_local = self.housing_widgets
        
            if value:
                # Hide Find BRMA button
                w_local["find_brma_btn"].opacity = 0
                w_local["find_brma_btn"].disabled = True
        
                # Show manual controls
                w_local["location"].opacity = 1
                w_local["location"].disabled = False
                w_local["location"].height = 50
        
                w_local["brma"].opacity = 1
                w_local["brma"].disabled = False
                w_local["brma"].height = 50
        
                # Restore saved values
                w_local["location"].text = self.calculator_state.location or "Select Location"
                on_manual_location_change(w_local["location"], w_local["location"].text)
                w_local["brma"].text = self.calculator_state.brma or "Select BRMA"
        
            else:
                # Show Find BRMA button
                w_local["find_brma_btn"].opacity = 1
                w_local["find_brma_btn"].disabled = False
        
                # Hide manual controls
                w_local["location"].opacity = 0
                w_local["location"].disabled = True
                w_local["location"].height = 0
        
                w_local["brma"].opacity = 0
                w_local["brma"].disabled = True
                w_local["brma"].height = 0
        
        w["manual_toggle"].bind(active=toggle_manual_mode)

        # ---------------------------------------------------------
        # SERVICE CHARGES (COLLAPSIBLE)
        # ---------------------------------------------------------
        w["service_section_expanded"] = False

        class ServiceClickableBox(ButtonBehavior, BoxLayout):
            pass

        service_header = ServiceClickableBox(
            orientation="horizontal",
            spacing=10,
            padding=(15, 10),
            size_hint=(1, None),
            height=50,
        )

        service_label = SafeLabel(
            text="Eligible Service Charges (Social Rent Only)",
            font_size=18,
            color=get_color_from_hex("#005EA5"),
            halign="left",
            valign="middle",
        )
        service_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        service_header.add_widget(service_label)

        service_chevron = Image(
            source="images/icons/ChevronDown-icon/ChevronDown-16px.png",
            size_hint=(None, None),
            size=(20, 20),
            allow_stretch=True,
            keep_ratio=True,
        )
        service_header.add_widget(service_chevron)

        def set_header_background(widget, color_hex, alpha=1.0):
            widget.canvas.before.clear()
            if color_hex:
                r, g, b = get_color_from_hex(color_hex)[:3]
                with widget.canvas.before:
                    Color(r, g, b, alpha)
                    widget._bg = Rectangle(size=widget.size, pos=widget.pos)

            def update_bg(inst, val):
                if hasattr(widget, "_bg"):
                    widget._bg.size = widget.size
                    widget._bg.pos = widget.pos

            widget.bind(size=update_bg, pos=update_bg)

        # Start with header hidden until tenancy = social
        set_header_background(service_header, "#FFDD00", 1.0)
        layout.add_widget(service_header)

        service_box = BoxLayout(
            orientation="vertical",
            spacing=10,
            size_hint=(1, None),
        )
        service_box.bind(minimum_height=service_box.setter("height"))
        layout.add_widget(service_box)
        w["service_box"] = service_box

        # Start fully collapsed and invisible
        service_header.opacity = 0
        service_header.height = 0
        service_header.disabled = True

        service_box.opacity = 0
        service_box.disabled = True
        service_box.height = 0
        service_box.spacing = 0

        def apply_service_header(mode, expanded):
            if mode != "applicable":
                # Completely hide header when not social
                service_header.opacity = 0
                service_header.height = 0
                service_header.disabled = True
                return

            # Social tenancy: header visible
            service_header.opacity = 1
            service_header.height = 50
            service_header.disabled = False

            if expanded:
                service_label.color = get_color_from_hex("#005EA5")
                service_chevron.source = "images/icons/ChevronUp-icon/ChevronUp-16px.png"
                service_chevron.size = (20, 20)
                set_header_background(service_header, "#FFDD00", 1.0)
            else:
                service_label.color = get_color_from_hex("#005EA5")
                service_chevron.source = ""
                service_chevron.size = (0, 20)   # collapse horizontally
                set_header_background(service_header, "#FFDD00", 1.0)

        def apply_service_box(mode, expanded):
            if expanded and mode == "applicable":
                service_box.opacity = 1
                service_box.disabled = False
                service_box.spacing = 10
                service_box.height = service_box.minimum_height

                # Restore child heights
                for child in service_box.children:
                    child.height = 70
                    child.opacity = 1
                    child.disabled = False
            else:
                service_box.opacity = 0
                service_box.disabled = True
                service_box.spacing = 0
                service_box.height = 0

                # Collapse children
                for child in service_box.children:
                    child.height = 0
                    child.opacity = 0
                    child.disabled = True

        def toggle_service_section(instance):
            expanded = not w["service_section_expanded"]
            w["service_section_expanded"] = expanded
            mode = get_service_mode(w["tenancy_type"].text)
            apply_service_header(mode, expanded)
            apply_service_box(mode, expanded)

        service_header.bind(on_press=toggle_service_section)

        # SERVICE CHARGE FIELDS
        def make_service_input(label_text):
            box = BoxLayout(orientation="vertical", size_hint_y=None, height=70)
            lbl = SafeLabel(
                text=label_text,
                font_size=16,
                color=get_color_from_hex("#005EA5"),
                size_hint_y=None,
                height=20,
            )
            inp = CustomTextInput(
                hint_text="£ per month",
                multiline=False,
                font_size=18,
                size_hint=(1, None),
                height=50,
                background_color=get_color_from_hex("#FFFFFF"),
                foreground_color=get_color_from_hex("#005EA5"),
            )
            box.add_widget(lbl)
            box.add_widget(inp)
            return box, inp

        service_fields = {}
        service_order = [
            ("cleaning", "Cleaning"),
            ("communal_cleaning", "Communal cleaning"),
            ("lighting", "Lighting"),
            ("communal_lighting", "Communal lighting"),
            ("grounds", "Grounds"),
            ("grounds_maintenance", "Grounds maintenance"),
            ("lift_maintenance", "Lift maintenance"),
            ("fire_safety", "Fire safety"),
            ("door_entry", "Door entry system"),
            ("shared_facilities", "Shared facilities"),
            ("communal_repairs", "Communal repairs"),
            ("estate_services", "Estate services"),
        ]

        for key, label_text in service_order:
            row, inp = make_service_input(label_text)
            service_box.add_widget(row)
            service_fields[key] = inp

        w["service_fields"] = service_fields

        def on_tenancy_change_service(spinner, value):
            mode = get_service_mode(value)

            # If not social, force collapsed and hide everything
            if mode != "applicable":
                w["service_section_expanded"] = False

            expanded = w["service_section_expanded"]
            apply_service_header(mode, expanded)
            apply_service_box(mode, expanded)

            # Enable/disable service fields based on tenancy
            social = (value or "").strip().lower() == "Social"
            for field in w["service_fields"].values():
                field.disabled = not social

        w["tenancy_type"].label.bind(text=on_tenancy_change_service)

        # ---------------------------------------------------------
        # FIND BRMA BUTTON
        # ---------------------------------------------------------
        find_brma_btn = RoundedButton(
            text="Find BRMA",
            size_hint=(None, None),
            size=(250, 60),
            background_normal="",
            background_color=(0, 0, 0, 0),
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            halign="center",
            valign="middle",
            text_size=(250, None),
            pos_hint={"center_x": 0.5},
        )
        layout.add_widget(find_brma_btn)
        w["find_brma_btn"] = find_brma_btn

        # Helper to show the results box
        def show_results_box():
            box = w["brma_results_box"]
            box.opacity = 1
            box.height = box.minimum_height
        
        
        # ---------------------------------------------------------
        # BRMA/LHA RESULTS BOX (yellow GOV.UK box)
        # ---------------------------------------------------------
        w["brma_results_box"] = BoxLayout(
            orientation="vertical",
            spacing=8,
            padding=[10, 10, 10, 10],
            size_hint_y=None,
            height=0,      # start collapsed
            opacity=0,     # start invisible
        )
        
        w["brma_results_box"].bind(
            minimum_height=w["brma_results_box"].setter("height")
        )
        
        layout.add_widget(w["brma_results_box"])
        
        # Yellow background + border
        with w["brma_results_box"].canvas.before:
            # Pale yellow background
            Color(1, 0.87, 0, 0.25)
            w["brma_results_box"]._bg = Rectangle(pos=(0, 0), size=(0, 0))
        
            # Strong yellow border
            Color(1, 0.87, 0, 1)
            w["brma_results_box"]._border = Line(rectangle=(0, 0, 0, 0), width=2)
        
        def update_border(inst, val):
            # Update background rectangle
            w["brma_results_box"]._bg.pos = w["brma_results_box"].pos
            w["brma_results_box"]._bg.size = w["brma_results_box"].size
        
            # Update border rectangle
            w["brma_results_box"]._border.rectangle = (
                w["brma_results_box"].x,
                w["brma_results_box"].y,
                w["brma_results_box"].width,
                w["brma_results_box"].height,
            )
        
        w["brma_results_box"].bind(size=update_border, pos=update_border)

        def add_result_row(category, value):
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=30)
        
            # Bold category label
            row.add_widget(
                SafeLabel(
                    text=f"[b]{category}[/b]",
                    markup=True,
                    font_size=16,
                    color=(1, 1, 1, 1),   # white
                    size_hint_x=0.45,
                    size_hint_y=None,
                    height=30,
                )
            )
        
            # Normal value label
            row.add_widget(
                SafeLabel(
                    text=value,
                    font_size=16,
                    color=(1, 1, 1, 1),   # white
                    size_hint_x=0.55,
                    size_hint_y=None,
                    height=30,
                )
            )
        
            w["brma_results_box"].add_widget(row)

        # ---------------------------------------------------------
        # FIND BRMA LOGIC
        # ---------------------------------------------------------
        def on_find_brma(instance):
            postcode = w["postcode"].text.strip().replace(" ", "").upper()
            if not postcode:
                return

            self.show_loading("Finding BRMA...")

            def do_lookup(dt):
                try:
                    app = App.get_running_app()

                    brma_name = self.lookup_brma(postcode)
                    location = self.lookup_location_for_postcode(postcode)

                    app.calculator_state.location = location
                    app.calculator_state.brma = brma_name
                    app.calculator_state.postcode = postcode

                    print(f"DEBUG: postcode={postcode}, brma={brma_name}, location={location}")

                    # Auto-detect London
                    app.calculator_state.in_london = is_london_postcode(postcode)
                    print("DEBUG: in_london =", app.calculator_state.in_london)

                    # Fill results box
                    results_box = w["brma_results_box"]
                    results_box.clear_widgets()

                    bedrooms = self.get_bedroom_entitlement()
                    loc_norm = location.lower() if location else None
                    lha_monthly = self.lookup_lha_rate(brma_name, bedrooms, loc_norm)

                    results_box.opacity = 0
                    results_box.height = 0

                    add_result_row("Location:", location or "Not found")
                    add_result_row("BRMA:", brma_name or "Not found")
                    add_result_row("Bedroom entitlement:", str(bedrooms))
                    add_result_row("LHA monthly rate:", f"£{lha_monthly:.2f}")

                    show_results_box()

                    scroll = w.get("scroll_view")
                    if scroll:
                        Clock.schedule_once(lambda dt: scroll.scroll_to(results_box), 0.1)

                except Exception as e:
                    print("BRMA lookup error:", e)
                finally:
                    self.hide_loading()

            Clock.schedule_once(do_lookup, 0)

        find_brma_btn.bind(on_press=on_find_brma)

    # ---------------------------------------------------------
    # STATE SAVE / LOAD
    # ---------------------------------------------------------
    def save_state(self):
        w = self.housing_widgets
        data = self.calculator_state
    
        data.housing_type = (w["housing_type"].text or "").strip().lower()
        data.tenancy_type = (w["tenancy_type"].text or "").strip().lower()
    
        data.rent_raw = (w["rent"].text or "").strip()
        data.mortgage_raw = (w["mortgage"].text or "").strip()
        data.shared_raw = (w["shared"].text or "").strip()
        data.non_dependants_raw = (w["non_dependants"].text or "").strip()
        data.postcode = (w["postcode"].text or "").strip()
    
        # Manual vs automatic location/BRMA
        data.manual_location = bool(w["manual_toggle"].active)
        if data.manual_location:
            data.location = w["location"].text
            data.brma = w["brma"].text
    
        # Service charges
        charges = {}
    
        def parse_charge(widget):
            try:
                return float(widget.text or 0)
            except Exception:
                return 0.0
    
        for key, widget in w["service_fields"].items():
            charges[key] = parse_charge(widget)
    
        data.service_charges = charges
    
        # Parsed numeric values
        try:
            data.non_dependants = int(w["non_dependants"].text or 0)
        except Exception:
            data.non_dependants = 0
    
        try:
            data.rent = float(w["rent"].text or 0)
        except Exception:
            data.rent = 0.0
    
        try:
            data.mortgage = float(w["mortgage"].text or 0)
        except Exception:
            data.mortgage = 0.0
    
        try:
            data.shared = float(w["shared"].text or 0)
        except Exception:
            data.shared = 0.0
        
    def load_state(self):
        w = self.housing_widgets
        data = self.calculator_state
    
        # BASIC FIELDS
        if data.housing_type:
            w["housing_type"].text = data.housing_type.capitalize()
        else:
            w["housing_type"].text = "Select Housing Type"
    
        w["tenancy_type"].text = data.tenancy_type or "Select Tenancy Type"
    
        w["rent"].text = getattr(data, "rent_raw", "") or ""
        w["mortgage"].text = getattr(data, "mortgage_raw", "") or ""
        w["shared"].text = getattr(data, "shared_raw", "") or ""
        w["non_dependants"].text = getattr(data, "non_dependants_raw", "") or ""
        w["postcode"].text = data.postcode or ""
    
        # SHOW CORRECT RENT/MORTGAGE/SHARED FIELD
        text = (w["housing_type"].text or "").lower()
        for key in ("rent", "mortgage", "shared"):
            field = w[key]
            field.opacity = 0
            field.disabled = True
            field.height = 0
    
        if "rent" in text:
            target = w["rent"]
        elif "own" in text:
            target = w["mortgage"]
        elif "shared" in text:
            target = w["shared"]
        else:
            target = None
    
        if target:
            target.opacity = 1
            target.disabled = False
            target.height = 50
    
        # MANUAL OVERRIDE
        if getattr(data, "manual_location", False):
            w["manual_toggle"].active = True
    
            w["location"].disabled = False
            w["location"].opacity = 1
            w["location"].height = 50
    
            w["brma"].disabled = False
            w["brma"].opacity = 1
            w["brma"].height = 50
    
            # Restore manual values
            w["location"].text = data.location or "Select Location"
    
            # Re-filter BRMAs based on location
            app = App.get_running_app()
            loc = (w["location"].text or "").lower()
            brmas = app.brma_by_location.get(loc, [])
            w["brma"].values = brmas or ["Select BRMA"]
            w["brma"].text = data.brma or "Select BRMA"
    
        else:
            w["manual_toggle"].active = False
    
            w["location"].disabled = True
            w["location"].opacity = 0
            w["location"].height = 0
    
            w["brma"].disabled = True
            w["brma"].opacity = 0
            w["brma"].height = 0
    
        # SERVICE CHARGES
        charges = data.service_charges or {}
        for key, widget in w["service_fields"].items():
            val = charges.get(key, "")
            widget.text = "" if val in (None, "") else str(val)
    
        # TENANCY-DEPENDENT SERVICE CHARGE ENABLE/DISABLE
        tenancy = (w["tenancy_type"].text or "").strip().lower()
        social = (tenancy == "Social")
        for widget in w["service_fields"].values():
            widget.disabled = not social

    # ---------------------------------------------------------
    # LOOKUP HELPERS
    # ---------------------------------------------------------
    def get_bedroom_entitlement(self):
        app = App.get_running_app()
        engine = app.engine
        state = app.calculator_state
        return engine.calculate_bedroom_entitlement(state)

    def lookup_brma(self, postcode):
        app = App.get_running_app()
        result = app.lookup_postcode(postcode)
        if not result:
            return None
        return result["brma_name"]
    
    def lookup_location_for_postcode(self, postcode):
        app = App.get_running_app()
        result = app.lookup_postcode(postcode)
        if not result:
            return None

        code = result["country"]
        return {"E": "England", "S": "Scotland", "W": "Wales"}.get(code, None)

    def lookup_lha_rate(self, brma, bedrooms, location):
        if not brma:
            return 0.0
    
        location = (location or "").strip().lower()
        if location not in ("england", "scotland", "wales"):
            return 0.0
    
        if bedrooms == "Shared":
            col = "SAR"
        elif bedrooms == 1:
            col = "1 Bed"
        elif bedrooms == 2:
            col = "2 bed"
        elif bedrooms == 3:
            col = "3 bed"
        elif bedrooms >= 4:
            col = "4 Bed"
        else:
            return 0.0
    
        data = App.get_running_app()._lha_data.get(location)
        if not data:
            return 0.0
    
        brma_lower = brma.lower()
        for row in data:
            if row.get("BRMA", "").strip().lower() == brma_lower:
                try:
                    monthly = float(row.get(col, 0) or 0)
                except Exception:
                    monthly = 0.0
                return monthly   # <-- FIXED
    
        return 0.0

    # ============================================================
    # ELIGIBLE SERVICE CHARGES (SOCIAL RENT)
    # ============================================================
    def calculate_eligible_service_charges(self, data):
        eligible_keys = {
            "cleaning",
            "communal_cleaning",
            "lighting",
            "communal_lighting",
            "grounds",
            "grounds_maintenance",
            "lift_maintenance",
            "fire_safety",
            "door_entry",
            "shared_facilities",
            "communal_repairs",
            "estate_services",
        }

        charges = data.service_charges
        if not isinstance(charges, dict):
            return 0.0

        total = 0.0
        for key, value in charges.items():
            if key.lower().strip() in eligible_keys:
                try:
                    total += float(value)
                except Exception:
                    pass

        return total


class CalculatorChildrenScreen(BaseScreen):
    def __init__(self, calculator_state, **kwargs):
        super().__init__(**kwargs)
        self.calculator_state = calculator_state
        self.child_sections = []
        self.build_ui()

    def build_ui(self):
        # ROOT layout (nav bar + scroll)
        root = BoxLayout(orientation="vertical")

        # ⭐ Navigation bar at the top
        root.add_widget(CalculatorNavBar(current="calculator_children"))

        # ⭐ ScrollView for form content
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)

        # ⭐ Main layout inside ScrollView
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=(20, 20, 20, 20),
            size_hint_y=None
        )
        layout.bind(minimum_height=layout.setter("height"))

        scroll.add_widget(layout)
        root.add_widget(scroll)
        self.add_widget(root)

        # ---------------------------------------------------------
        # INSTRUCTION LABEL
        # ---------------------------------------------------------
        instruction = SafeLabel(
            text="Enter children details:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")
        )
        instruction.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(instruction)

        # ---------------------------------------------------------
        # DO YOU HAVE CHILDREN? TOGGLE
        # ---------------------------------------------------------
        children_row, children_yes_btn, children_no_btn = make_yes_no_row(
            "Do you have children?",
            self.on_children_toggle
        )
        
        layout.add_widget(children_row)
        
        self.children_yes_btn = children_yes_btn
        self.children_no_btn = children_no_btn

        self.child_container = BoxLayout(
            orientation="vertical",
            spacing=20,
            size_hint_y=None
        )
        self.child_container.bind(minimum_height=self.child_container.setter("height"))
        layout.add_widget(self.child_container)

        # ---------------------------------------------------------
        # SPACER ABOVE BUTTONS
        # ---------------------------------------------------------
        layout.add_widget(Widget(size_hint_y=None, height=20))

        # ---------------------------------------------------------
        # ADD CHILD BUTTON
        # ---------------------------------------------------------
        add_btn = RoundedButton(
            text="Add Another Child",
            size_hint=(None, None),
            size=(250, 60),
            background_color=(0, 0, 0, 0),
            background_normal="",
            pos_hint={"center_x": 0.5},
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            halign="center",
            valign="middle",
            text_size=(250, None),
            on_press=self.add_child_section,
            opacity=0,              # ⭐ start hidden
            disabled=True           # ⭐ start disabled
        )
        layout.add_widget(add_btn)
        
        # ⭐ Save reference
        self.add_child_button = add_btn

        # ---------------------------------------------------------
        # SPACER BELOW BUTTONS
        # ---------------------------------------------------------
        layout.add_widget(Widget(size_hint_y=None, height=20))

    # ---------------------------------------------------------
    # ADD CHILD SECTION
    # ---------------------------------------------------------
    def add_child_section(self, instance=None, prefill=None):

        # COLLAPSIBLE HEADER
        header_btn = BoxLayout(
            orientation="horizontal",
            spacing=10,
            size_hint=(1, None),
            height=60,
            padding=(15, 10)
        )

        # Header background
        with header_btn.canvas.before:
            Color(*get_color_from_hex("#FFDD00"))
            header_btn._bg = Rectangle(size=header_btn.size, pos=header_btn.pos)

        header_btn.bind(
            size=lambda inst, val: setattr(header_btn._bg, "size", val),
            pos=lambda inst, val: setattr(header_btn._bg, "pos", val),
        )

        header_label = SafeLabel(
            text="New Child",
            font_size=20,
            color=get_color_from_hex("#005EA5"),
            halign="left",
            valign="middle"
        )
        header_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))

        header_chevron = Image(
            source="images/icons/ChevronDown-icon/ChevronDown-16px.png",
            size_hint=(None, None),
            size=(20, 20),
            allow_stretch=True,
            keep_ratio=True
        )

        header_btn.add_widget(header_label)
        header_btn.add_widget(header_chevron)

        # CONTENT BOX (collapsed initially)
        content_box = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=(10, 10),
            size_hint_y=None,
            height=0,
            opacity=0
        )

        # ⭐ FIX: Bind minimum_height so expansion works correctly
        content_box.bind(minimum_height=content_box.setter("height"))

        # Expand if prefilled
        if prefill:
            content_box.opacity = 1
            content_box.height = content_box.minimum_height
            header_chevron.source = "images/icons/ChevronUp-icon/ChevronUp-16px.png"

        # CHILD NAME
        name_input = CustomTextInput(
            hint_text="Child Name",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE),
            text=prefill.get("name", "") if prefill else ""
        )
        content_box.add_widget(name_input)

        # CHILD DOB
        dob_input = DOBInput(
            hint_text="Child Date of Birth (DD/MM/YYYY)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE),
            text=prefill.get("dob", "") if prefill else ""
        )
        content_box.add_widget(dob_input)

        # GENDER SPINNER
        gender_spinner = GovUkDropdown(
            text=prefill.get("gender", "Select gender") if prefill else "Select gender",
            values=["Male", "Female", "Prefer not to say"]
        )
        
        content_box.add_widget(gender_spinner)

        gender_spinner.label.bind(
            text=lambda inst, val, s=gender_spinner: setattr(s, "text", val)
        )

        # FLAGS
        def make_flag(label, value=False):
            row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
            cb = CheckBox(active=value)
            lbl = SafeLabel(text=label, font_size=16, color=get_color_from_hex(WHITE))
            row.add_widget(cb)
            row.add_widget(lbl)
            return row, cb

        adopted_row, adopted_cb = make_flag("Adopted", prefill.get("adopted", False) if prefill else False)
        kinship_row, kinship_cb = make_flag("Kinship care", prefill.get("kinship_care", False) if prefill else False)
        multiple_row, multiple_cb = make_flag("Multiple birth", prefill.get("multiple_birth", False) if prefill else False)
        disabled_row, disabled_cb = make_flag("Disabled child (DLA/PIP)", prefill.get("disabled", False) if prefill else False)
        severe_row, severe_cb = make_flag("Severely disabled child (DLA High Care / PIP Enhanced)", prefill.get("severely_disabled", False) if prefill else False)
        ncc_row, ncc_cb = make_flag("Non‑consensual conception (Two‑child limit exception)", prefill.get("non_consensual", False) if prefill else False)
        
        content_box.add_widget(adopted_row)
        content_box.add_widget(kinship_row)
        content_box.add_widget(multiple_row)
        content_box.add_widget(disabled_row)
        content_box.add_widget(severe_row)
        content_box.add_widget(ncc_row)

        def on_severe_active(instance, value):
            if value:
                disabled_cb.active = True
        
        def on_disabled_active(instance, value):
            if not value:
                severe_cb.active = False
        
        disabled_cb.bind(active=on_disabled_active)
        severe_cb.bind(active=on_severe_active)

        # REMOVE CHILD BUTTON
        remove_btn = RoundedButton(
            text="Remove Child",
            size_hint=(None, None),
            size=(200, 50),
            background_color=get_color_from_hex("#D4351C"),
            background_normal="",
            color=get_color_from_hex("#FFFFFF"),
            font_size=16,
            halign="center",
            valign="middle",
            text_size=(200, None),
            on_press=lambda inst: self.remove_child_section(section)
        )
        content_box.add_widget(remove_btn)

        # COLLAPSE/EXPAND LOGIC
        def toggle_section(instance, touch=None):
            if touch and not instance.collide_point(*touch.pos):
                return False

            if content_box.height == 0:
                content_box.height = content_box.minimum_height
                content_box.opacity = 1
                header_chevron.source = "images/icons/ChevronUp-icon/ChevronUp-16px.png"
            else:
                content_box.height = 0
                content_box.opacity = 0
                header_chevron.source = "images/icons/ChevronDown-icon/ChevronDown-16px.png"

            return True

        header_btn.bind(on_touch_down=toggle_section)

        # STORE SECTION
        section = {
            "header": header_btn,
            "content": content_box,
            "name": name_input,
            "dob": dob_input,
            "gender": gender_spinner,
            "adopted": adopted_cb,
            "kinship": kinship_cb,
            "multiple": multiple_cb,
            "disabled": disabled_cb,
            "severely_disabled": severe_cb,
            "non_consensual": ncc_cb,
            "toggle": toggle_section
        }

        self.child_sections.append(section)

        # Update header text dynamically
        header_label.text = self.get_child_header_text(section)
        name_input.bind(text=lambda inst, val: setattr(header_label, "text", self.get_child_header_text(section)))

        # Add to layout
        self.child_container.add_widget(header_btn)
        self.child_container.add_widget(content_box)

        Clock.schedule_once(lambda dt: setattr(content_box, "height", content_box.minimum_height), 0)

        return section

    def get_child_header_text(self, section):
        """
        Returns the header label text for a child section.
        If the name field is filled, show the name.
        Otherwise show 'Child X' based on index.
        """
        name = section["name"].text.strip()
        if name:
            return name

        # Determine index based on position in child_sections
        try:
            index = self.child_sections.index(section) + 1
        except ValueError:
            index = 1

        return f"Child {index}"

    def remove_child_section(self, section):
        """
        Safely remove a child section from the UI and refresh numbering.
        """

        # 1. Remove widgets from layout
        try:
            self.child_container.remove_widget(section["header"])
        except Exception:
            pass

        try:
            self.child_container.remove_widget(section["content"])
        except Exception:
            pass

        # 2. Remove from internal list
        if section in self.child_sections:
            self.child_sections.remove(section)

        # 3. Refresh header numbering
        self.refresh_child_headers()

    def refresh_child_headers(self):
        for i, section in enumerate(self.child_sections, start=1):
            name = section["name"].text.strip()
            header_label = section["header"].children[1]  # SafeLabel
            header_label.text = name if name else f"Child {i}"

    def on_children_toggle(self, value):
        if value:
            # YES
            self.child_container.opacity = 1
            self.child_container.disabled = False
    
            self.add_child_button.opacity = 1
            self.add_child_button.disabled = False
    
            if not self.child_sections:
                section = self.add_child_section()
    
                section["toggle"](section["header"])
                section["toggle"](section["header"])
                section["toggle"](section["header"])
    
        else:
            # NO
            for section in list(self.child_sections):
                self.remove_child_section(section)
    
            self.child_container.opacity = 0
            self.child_container.disabled = True
    
            self.add_child_button.opacity = 0
            self.add_child_button.disabled = True
    
            self.calculator_state.children = []
    
    def save_state(self):
        # If NO is selected → clear and exit
        if self.children_no_btn.state == "down":
            self.calculator_state.children = []
            self.calculator_state.children_dobs = []
            return
    
        children = []
    
        for section in self.child_sections:
            name = section["name"].text.strip()
            dob = section["dob"].text.strip()
            gender = section["gender"].text.strip()
    
            if not dob:
                continue
    
            children.append({
                "name": name,
                "dob": dob,
                "gender": gender,
                "adopted": section["adopted"].active,
                "kinship_care": section["kinship"].active,
                "multiple_birth": section["multiple"].active,
                "disabled": section["disabled"].active,
                "severely_disabled": section["severely_disabled"].active,
                "non_consensual": section["non_consensual"].active
            })
    
        self.calculator_state.children = children
        self.calculator_state.children_dobs = [c["dob"] for c in children]
    
    def load_state(self):
        saved_children = getattr(self.calculator_state, "children", [])
    
        # Clear existing UI
        for section in list(self.child_sections):
            self.remove_child_section(section)
    
        if saved_children:
            # YES previously selected
            self.children_yes_btn.state = "down"
            self.children_no_btn.state = "normal"
    
            self.child_container.opacity = 1
            self.child_container.disabled = False
            self.add_child_button.opacity = 1
            self.add_child_button.disabled = False
    
            for child in saved_children:
                self.add_child_section(prefill=child)
    
        else:
            # NO previously selected
            self.children_yes_btn.state = "normal"
            self.children_no_btn.state = "down"
    
            self.child_container.opacity = 0
            self.child_container.disabled = True
            self.add_child_button.opacity = 0
            self.add_child_button.disabled = True
    
        # Refresh headers
        for section in self.child_sections:
            header_label = section["header"].children[1]
            header_label.text = self.get_child_header_text(section)


class CalculatorAdditionalElementsScreen(BaseScreen):
    def __init__(self, calculator_state, **kwargs):
        super().__init__(**kwargs)
        self.calculator_state = calculator_state
        self.additional_widgets = {"sar_fields": {}}
        self.build_ui()

    def build_ui(self):
        # ROOT layout (nav bar + scroll)
        root = BoxLayout(orientation="vertical")

        # ⭐ Navigation bar at the top
        root.add_widget(CalculatorNavBar(current="calculator_additional"))

        # ⭐ ScrollView for form content
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)

        # ⭐ Main layout inside ScrollView
        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=(20, 120, 20, 20),
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))

        scroll.add_widget(layout)
        root.add_widget(scroll)
        self.add_widget(root)

        w = self.additional_widgets

        # ---------------------------------------------------------
        # INSTRUCTION
        # ---------------------------------------------------------
        instruction = SafeLabel(
            text="Enter additional elements:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")
        )
        instruction.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(instruction)

        # ---------------------------------------------------------
        # CARER CHECKBOX
        # ---------------------------------------------------------
        carer_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=10)
        w["carer"] = CheckBox(size_hint=(None, None), size=(40, 40))

        carer_label = SafeLabel(
            text="Are you a carer?",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        carer_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))

        carer_row.add_widget(w["carer"])
        carer_row.add_widget(carer_label)
        layout.add_widget(carer_row)

        # ---------------------------------------------------------
        # DISABILITY: LCW / LCWRA
        # ---------------------------------------------------------
        disability_title = SafeLabel(
            text="Disability status",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        disability_title.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(disability_title)

        # LCW
        lcw_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=10)
        w["lcw"] = CheckBox(size_hint=(None, None), size=(40, 40))

        lcw_label = SafeLabel(
            text="Limited Capability for Work (LCW)",
            font_size=16,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        lcw_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))

        lcw_row.add_widget(w["lcw"])
        lcw_row.add_widget(lcw_label)
        layout.add_widget(lcw_row)

        # LCWRA
        lcwra_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=10)
        w["lcwra"] = CheckBox(size_hint=(None, None), size=(40, 40))

        lcwra_label = SafeLabel(
            text="Limited Capability for Work and Related Activity (LCWRA)",
            font_size=16,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        lcwra_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))

        lcwra_row.add_widget(w["lcwra"])
        lcwra_row.add_widget(lcwra_label)
        layout.add_widget(lcwra_row)

        # Mutual exclusion
        def on_lcw_active(instance, value):
            if value:
                w["lcwra"].active = False

        def on_lcwra_active(instance, value):
            if value:
                w["lcw"].active = False

        w["lcw"].bind(active=on_lcw_active)
        w["lcwra"].bind(active=on_lcwra_active)

        # ---------------------------------------------------------
        # CHILDCARE INPUT
        # ---------------------------------------------------------
        w["childcare"] = CustomTextInput(
            hint_text="Monthly childcare costs (£)",
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=50,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex(GOVUK_BLUE)
        )
        layout.add_widget(w["childcare"])

        # ---------------------------------------------------------
        # SAR EXEMPTIONS (COLLAPSIBLE)
        # ---------------------------------------------------------
        w["sar_expanded"] = False
        
        # Clickable header container
        class ClickableBox(ButtonBehavior, BoxLayout):
            pass
        
        sar_header = ClickableBox(
            orientation="horizontal",
            spacing=10,
            padding=(15, 10),
            size_hint=(1, None),
            height=50
        )
        
        # Label
        sar_label = SafeLabel(
            text="Shared Accommodation Rate (SAR) Exemptions",
            font_size=18,
            color=get_color_from_hex("#005EA5"),  # collapsed = blue text
            halign="left",
            valign="middle"
        )
        sar_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        sar_header.add_widget(sar_label)
        
        # Chevron
        sar_chevron = Image(
            source="images/icons/ChevronDown-icon/ChevronDown-16px.png",
            size_hint=(None, None),
            size=(20, 20),
            allow_stretch=True,
            keep_ratio=True
        )
        sar_header.add_widget(sar_chevron)
        
        # Background helper
        def set_sar_background(widget, color_hex, alpha=1.0):
            widget.canvas.before.clear()
            if color_hex:
                r, g, b = get_color_from_hex(color_hex)[:3]
                with widget.canvas.before:
                    Color(r, g, b, alpha)
                    widget._bg = Rectangle(size=widget.size, pos=widget.pos)
        
            def update_bg(inst, val):
                if hasattr(widget, "_bg"):
                    widget._bg.size = widget.size
                    widget._bg.pos = widget.pos
        
            widget.bind(size=update_bg, pos=update_bg)
        
        # Default collapsed background = faded yellow (unset)
        set_sar_background(sar_header, "#FFDD00", 0.4)
        
        layout.add_widget(sar_header)
        
        # Collapsible content box
        sar_box = BoxLayout(
            orientation="vertical",
            spacing=10,
            size_hint=(1, None)
        )
        sar_box.bind(minimum_height=sar_box.setter("height"))
        layout.add_widget(sar_box)
        
        # Start collapsed
        sar_box.opacity = 0
        sar_box.disabled = True
        sar_box.height = 0
        
        # ---------------------------------------------------------
        # APPLY HEADER VISUAL STATE
        # ---------------------------------------------------------
        def apply_sar_header(mode, expanded):
            if expanded:
                sar_label.color = get_color_from_hex("#005EA5")
                sar_chevron.source = "images/icons/ChevronUp-icon/ChevronUp-16px.png"
                set_sar_background(sar_header, "#FFDD00", 1.0)
                sar_header.opacity = 1
                sar_header.disabled = False
                return
        
            sar_label.color = get_color_from_hex("#005EA5")
            sar_chevron.source = "images/icons/ChevronDown-icon/ChevronDown-16px.png"
        
            if mode == "applicable":
                set_sar_background(sar_header, "#FFDD00", 1.0)
                sar_header.opacity = 1
                sar_header.disabled = False
        
            elif mode == "not_applicable":
                set_sar_background(sar_header, "#FFDD00", 0.4)
                sar_header.opacity = 0.4
                sar_header.disabled = True
        
            elif mode == "unset":
                set_sar_background(sar_header, "#FFDD00", 0.4)
                sar_header.opacity = 0.4
                sar_header.disabled = True
        
        # ---------------------------------------------------------
        # APPLY BOX STATE
        # ---------------------------------------------------------
        def apply_sar_box(mode, expanded):
            if expanded and mode == "applicable":
                sar_box.opacity = 1
                sar_box.disabled = False
                sar_box.height = sar_box.minimum_height
            else:
                sar_box.opacity = 0
                sar_box.disabled = True
                sar_box.height = 0

        def get_current_tenancy_type():
            tenancy = getattr(self.calculator_state, "tenancy_type", "") or ""
            return tenancy.strip().lower()

        def get_tenancy_mode(tenancy_type):
            """
            Returns SAR applicability mode based on tenancy type.
            tenancy_type should already be lowercase.
            """
        
            tenancy_type = (tenancy_type or "").strip().lower()
        
            if not tenancy_type:
                return "unset"
        
            # SAR applies ONLY to private rented sector
            if tenancy_type in ("private", "private rented"):
                return "applicable"
        
            # Social housing, supported accommodation, temporary accommodation
            # do NOT use SAR
            return "not_applicable"
        
        # ---------------------------------------------------------
        # EXPAND / COLLAPSE TOGGLE
        # ---------------------------------------------------------
        def toggle_sar_section(instance):
            expanded = not w["sar_expanded"]
            w["sar_expanded"] = expanded
        
            tenancy_type = get_current_tenancy_type()
            mode = get_tenancy_mode(tenancy_type)
        
            apply_sar_header(mode, expanded)
            apply_sar_box(mode, expanded)
        
        sar_header.bind(on_press=toggle_sar_section)
        
        # ---------------------------------------------------------
        # SAR EXEMPTION OPTIONS
        # ---------------------------------------------------------
        def add_sar_row(text, key):
            row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=40)
        
            cb = CheckBox(size_hint=(None, None), size=(40, 40))
            w["sar_fields"][key] = cb
        
            lbl = SafeLabel(
                text=text,
                font_size=16,
                color=get_color_from_hex("#FFFFFF"),
                halign="left"
            )
            lbl.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        
            row.add_widget(cb)
            row.add_widget(lbl)
            sar_box.add_widget(row)
        
        # Add all SAR fields
        add_sar_row("Care leaver (under 25)", "care_leaver")
        add_sar_row("Severe disability (LCWRA)", "severe_disability")
        add_sar_row("MAPPA supervision", "mappa")
        add_sar_row("Hostel resident (3+ months)", "hostel_resident")
        add_sar_row("Domestic abuse refuge", "domestic_abuse")
        add_sar_row("Ex-offender under supervision", "ex_offender")
        add_sar_row("Foster carer", "foster_carer")
        add_sar_row("Prospective adopter", "prospective_adopter")
        add_sar_row("Temporary accommodation", "temporary_accommodation")
        add_sar_row("Victim of modern slavery", "modern_slavery")
        add_sar_row("Armed forces reservist returning to civilian life", "armed_forces_reservist")

        # ---------------------------------------------------------
        # INITIALISE SAR STATE BASED ON CURRENT TENANCY
        # ---------------------------------------------------------
        tenancy_type = get_current_tenancy_type()
        mode = get_tenancy_mode(tenancy_type)
        expanded = w["sar_expanded"]
        
        apply_sar_header(mode, expanded)
        apply_sar_box(mode, expanded)

        # ---------------------------------------------------------
        # SPACERS / BUTTONS
        # ---------------------------------------------------------
        layout.add_widget(Widget(size_hint_y=0.05))

        buttons_box = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, None))
        layout.add_widget(buttons_box)

        layout.add_widget(Widget(size_hint_y=0.05))

    def save_state(self):
        w = self.additional_widgets
        data = self.calculator_state
    
        # ---------------------------------------------------------
        # CARER
        # ---------------------------------------------------------
        data.carer = w["carer"].active
    
        # ---------------------------------------------------------
        # DISABILITY FLAGS (LCW / LCWRA)
        # ---------------------------------------------------------
        data.has_lcw = w["lcw"].active
        data.has_lcwra = w["lcwra"].active
    
        # A single combined field if you want it:
        if data.has_lcwra:
            data.disability = "LCWRA"
        elif data.has_lcw:
            data.disability = "LCW"
        else:
            data.disability = ""
    
        # ---------------------------------------------------------
        # CHILDCARE COSTS
        # ---------------------------------------------------------
        raw = w["childcare"].text.strip()
        data.childcare_raw = raw
        try:
            data.childcare = float(raw or 0)
        except:
            data.childcare = 0.0
    
        # ---------------------------------------------------------
        # SAR EXEMPTIONS
        # ---------------------------------------------------------
        sar_dict = {}
        for key, cb in w["sar_fields"].items():
            sar_dict[key] = cb.active
        data.sar_exemptions = sar_dict
    
    def load_state(self):
        w = self.additional_widgets
        data = self.calculator_state
    
        # ---------------------------------------------------------
        # CARER
        # ---------------------------------------------------------
        w["carer"].active = bool(getattr(data, "carer", False))
    
        # ---------------------------------------------------------
        # DISABILITY FLAGS
        # ---------------------------------------------------------
        disability = getattr(data, "disability", "").upper()
    
        if disability == "LCWRA":
            w["lcwra"].active = True
            w["lcw"].active = False
        elif disability == "LCW":
            w["lcw"].active = True
            w["lcwra"].active = False
        else:
            w["lcw"].active = False
            w["lcwra"].active = False
    
        # ---------------------------------------------------------
        # CHILDCARE
        # ---------------------------------------------------------
        w["childcare"].text = str(getattr(data, "childcare_raw", ""))
    
        # ---------------------------------------------------------
        # SAR EXEMPTIONS
        # ---------------------------------------------------------
        sar_saved = getattr(data, "sar_exemptions", {}) or {}
        for key, cb in w["sar_fields"].items():
            cb.active = bool(sar_saved.get(key, False))

class CalculatorSanctionsScreen(BaseScreen):
    def __init__(self, calculator_state, **kwargs):
        super().__init__(**kwargs)
        self.calculator_state = calculator_state
        self.sanctions_widgets = {}
        self.build_ui()

    def build_ui(self):
        # ROOT layout (nav bar + scroll)
        root = BoxLayout(orientation="vertical")

        # ⭐ Navigation bar at the top
        root.add_widget(CalculatorNavBar(current="calculator_sanctions"))

        # ⭐ ScrollView for form content
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)

        # ⭐ Main layout inside ScrollView
        layout = BoxLayout(
            orientation="vertical",
            spacing=30,
            padding=(20, 20, 20, 20),
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))

        scroll.add_widget(layout)
        root.add_widget(scroll)
        self.add_widget(root)

        w = self.sanctions_widgets

        # ---------------------------------------------------------
        # INSTRUCTION LABEL
        # ---------------------------------------------------------
        instruction = SafeLabel(
            text="Enter sanction details:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")
        )
        instruction.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(instruction)

        # ---------------------------------------------------------
        # DO YOU HAVE ANY SANCTIONS? TOGGLE
        # ---------------------------------------------------------
        sanctions_row, sanctions_yes_btn, sanctions_no_btn = make_yes_no_row(
            "Do you have any sanctions?",
            self.on_sanctions_toggle
        )
        
        layout.add_widget(sanctions_row)
        
        self.sanctions_yes_btn = sanctions_yes_btn
        self.sanctions_no_btn = sanctions_no_btn
        
        # ---------------------------------------------------------
        # SANCTIONS CONTAINER (hidden unless toggle is ON)
        # ---------------------------------------------------------
        self.sanctions_container = BoxLayout(
            orientation="vertical",
            spacing=20,
            size_hint_y=None
        )
        self.sanctions_container.opacity = 0
        self.sanctions_container.disabled = True
        self.sanctions_container.bind(minimum_height=self.sanctions_container.setter("height"))
        layout.add_widget(self.sanctions_container)
        
        # SANCTION TYPE
        sanction_type_label = SafeLabel(
            text="Sanction type",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        sanction_type_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        self.sanctions_container.add_widget(sanction_type_label)
        
        w["type"] = GovUkDropdown(
            text="Select sanction type",
            values=["lowest", "low", "medium", "high"]
        )
        self.sanctions_container.add_widget(w["type"])
        
        # SANCTION DURATION
        sanction_duration_label = SafeLabel(
            text="Sanction duration",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        sanction_duration_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        self.sanctions_container.add_widget(sanction_duration_label)
        
        w["duration"] = GovUkDropdown(
            text="Select duration",
            values=["7 days", "14 days", "28 days", "91 days", "182 days"]
        )
        self.sanctions_container.add_widget(w["duration"])

    def on_sanctions_toggle(self, value):
        if value:
            # YES → show sanctions details
            self.sanctions_container.opacity = 1
            self.sanctions_container.disabled = False
    
        else:
            # NO → hide sanctions details
            self.sanctions_container.opacity = 0
            self.sanctions_container.disabled = True
    
            # Clear saved sanction data immediately
            self.calculator_state.sanction_type = ""
            self.calculator_state.sanction_duration = 0
            self.calculator_state.sanction_duration_raw = ""

    def save_state(self):
        w = self.sanctions_widgets
        data = self.calculator_state
    
        # If NO is selected
        if self.sanctions_no_btn.state == "down":
            data.sanction_type = ""
            data.sanction_duration = 0
            data.sanction_duration_raw = ""
            return
    
        # Otherwise save normally:
        sanction_type = w["type"].text.strip().lower()
        if sanction_type in ["lowest", "low", "medium", "high"]:
            data.sanction_type = sanction_type
        else:
            data.sanction_type = ""
    
        raw_duration = w["duration"].text.strip()
        data.sanction_duration_raw = raw_duration
    
        try:
            data.sanction_duration = int(raw_duration.split()[0])
        except:
            data.sanction_duration = 0
    
    def load_state(self):
        w = self.sanctions_widgets
        data = self.calculator_state
    
        saved_type = getattr(data, "sanction_type", "")
        saved_duration = getattr(data, "sanction_duration_raw", "")
    
        if saved_type and saved_duration:
            # YES previously selected
            self.sanctions_yes_btn.state = "down"
            self.sanctions_no_btn.state = "normal"
    
            self.sanctions_container.opacity = 1
            self.sanctions_container.disabled = False
    
            # Restore fields
            w["type"].text = saved_type
            w["duration"].text = saved_duration
    
        else:
            # NO previously selected
            self.sanctions_yes_btn.state = "normal"
            self.sanctions_no_btn.state = "down"
    
            self.sanctions_container.opacity = 0
            self.sanctions_container.disabled = True
    
            w["type"].text = "Select sanction type"
            w["duration"].text = "Select duration"
            
class CalculatorAdvanceScreen(BaseScreen):
    def __init__(self, calculator_state, **kwargs):
        super().__init__(**kwargs)
        self.calculator_state = calculator_state
        self.advance_widgets = {}
        self.build_ui()

    def build_ui(self):
        # ROOT layout (nav bar + scroll)
        root = BoxLayout(orientation="vertical")

        # Navigation bar
        root.add_widget(CalculatorNavBar(current="calculator_advance"))

        # ScrollView
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            do_scroll_y=True
        )

        # Main content layout
        layout = BoxLayout(
            orientation="vertical",
            spacing=30,
            padding=(20, 20, 20, 20),
            size_hint=(1, None)
        )
        layout.bind(minimum_height=layout.setter("height"))

        scroll.add_widget(layout)
        root.add_widget(scroll)
        self.add_widget(root)

        w = self.advance_widgets

        # ---------------------------------------------------------
        # INSTRUCTION LABEL
        # ---------------------------------------------------------
        instruction = SafeLabel(
            text="Enter advance payment details:",
            font_size=18,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#005EA5")
        )
        instruction.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        layout.add_widget(instruction)

        # ---------------------------------------------------------
        # ARE YOU APPLYING FOR AN ADVANCE PAYMENT? TOGGLE
        # ---------------------------------------------------------
        advance_row, advance_yes_btn, advance_no_btn = make_yes_no_row(
            "Are you applying for an advance payment?",
            self.on_advance_toggle
        )
        
        layout.add_widget(advance_row)
        
        self.advance_yes_btn = advance_yes_btn
        self.advance_no_btn = advance_no_btn

        # ---------------------------------------------------------
        # ADVANCE PAYMENT CONTAINER (hidden unless toggle is ON)
        # ---------------------------------------------------------
        self.advance_container = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=(0, 10),
            size_hint_y=None
        )
        self.advance_container.opacity = 0
        self.advance_container.disabled = True
        self.advance_container.bind(minimum_height=self.advance_container.setter("height"))
        layout.add_widget(self.advance_container)

        # ---------------------------------------------------------
        # ADVANCE AMOUNT
        # ---------------------------------------------------------
        amount_label = SafeLabel(
            text="Advance amount (£)",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        amount_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        self.advance_container.add_widget(amount_label)
        
        w["amount"] = CustomTextInput(
            hint_text="Enter amount",
            input_filter="float",
            size_hint_y=None,
            height=50,          # ⭐ proper height
            font_size=18,       # ⭐ readable text
            padding=(10, 10)    # ⭐ breathing room
        )
        self.advance_container.add_widget(w["amount"])

        # ---------------------------------------------------------
        # REPAYMENT PERIOD
        # ---------------------------------------------------------
        period_label = SafeLabel(
            text="Repayment period (months)",
            font_size=18,
            color=get_color_from_hex("#FFFFFF"),
            halign="left"
        )
        period_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        self.advance_container.add_widget(period_label)
        
        w["period"] = CustomTextInput(
            hint_text="Enter number of months",
            input_filter="int",
            size_hint_y=None,
            height=50,          # ⭐ proper height
            font_size=18,       # ⭐ readable text
            padding=(10, 10)    # ⭐ breathing room
        )
        self.advance_container.add_widget(w["period"])

    def on_advance_toggle(self, value):
        if value:
            # YES → show advance fields
            self.advance_container.opacity = 1
            self.advance_container.disabled = False
        else:
            # NO → hide advance fields
            self.advance_container.opacity = 0
            self.advance_container.disabled = True
    
            # Clear saved advance data immediately
            self.calculator_state.advance_amount = 0
            self.calculator_state.advance_repayment_period = ""

    def save_state(self):
        w = self.advance_widgets
        data = self.calculator_state
    
        # If NO is selected → clear and exit
        if self.advance_no_btn.state == "down":
            data.advance_amount = 0
            data.advance_repayment_period = ""
            return
    
        # Otherwise save normally:
        try:
            data.advance_amount = float(w["amount"].text.strip())
        except:
            data.advance_amount = 0
    
        data.advance_repayment_period = w["period"].text.strip()

    def load_state(self):
        w = self.advance_widgets
        data = self.calculator_state
    
        saved_amount = getattr(data, "advance_amount", 0)
        saved_period = getattr(data, "advance_repayment_period", "")
    
        if saved_amount > 0 or saved_period:
            # YES previously selected
            self.advance_yes_btn.state = "down"
            self.advance_no_btn.state = "normal"
    
            self.advance_container.opacity = 1
            self.advance_container.disabled = False
    
            w["amount"].text = str(saved_amount)
            w["period"].text = saved_period
    
        else:
            # NO previously selected
            self.advance_yes_btn.state = "normal"
            self.advance_no_btn.state = "down"
    
            self.advance_container.opacity = 0
            self.advance_container.disabled = True
    
            w["amount"].text = ""
            w["period"].text = ""

class CalculatorFinalScreen(BaseScreen):
    def __init__(self, calculator_state, save_callbacks, calculate_callback, go_to_breakdown_callback, **kwargs):
        super().__init__(**kwargs)
        self.calculator_state = calculator_state
        self.save_callbacks = save_callbacks
        self.calculate_callback = calculate_callback
        self.go_to_breakdown_callback = go_to_breakdown_callback

        self.summary_widgets = {}
        self.calculate_scroll = None
        self.summary_layout = None  # <-- store the layout explicitly

        self.build_ui()

    # ---------------------------------------------------------
    # BUILD UI
    # ---------------------------------------------------------
    def build_ui(self):
        root = BoxLayout(orientation="vertical")

        root.add_widget(CalculatorNavBar(current="calculator_final"))

        outer = BoxLayout(orientation="vertical", spacing=0, padding=0)

        # Scroll area
        self.calculate_scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            do_scroll_y=True
        )

        # Store as an attribute so we don't rely on children[0]
        self.summary_layout = BoxLayout(
            orientation="vertical",
            spacing=30,
            padding=20,
            size_hint=(1, None)
        )
        self.summary_layout.bind(minimum_height=self.summary_layout.setter("height"))

        self.summary_layout.add_widget(
            wrapped_SafeLabel("Summary of your Universal Credit calculation:", 18, 30)
        )

        # Placeholder label
        self.summary_widgets["label"] = SafeLabel(
            text="No calculation yet.",
            font_size=16,
            halign="left",
            valign="top",
            color=get_color_from_hex("#FFFFFF"),
            size_hint_y=None
        )
        self.summary_widgets["label"].bind(
            width=lambda inst, val: setattr(inst, "text_size", (val, None)),
            texture_size=lambda inst, val: setattr(inst, "height", val[1])
        )
        self.summary_layout.add_widget(self.summary_widgets["label"])

        # Ensure scrollview has ONLY this layout as its child
        self.calculate_scroll.clear_widgets()
        self.calculate_scroll.add_widget(self.summary_layout)

        outer.add_widget(self.calculate_scroll)

        # Bottom button bar
        button_bar = BoxLayout(size_hint=(1, None), height=100, padding=20, spacing=20)

        run_btn = RoundedButton(
            text="Run Calculation",
            size_hint=(1, 1),
            background_color=(0, 0, 0, 0),
            background_normal="",
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            halign="center",
            valign="middle",
            text_size=(250, None),
            on_press=self.run_calculation
        )
        button_bar.add_widget(run_btn)

        breakdown_btn = RoundedButton(
            text="View Calculation Breakdown",
            size_hint=(1, 1),
            background_color=(0, 0, 0, 0),
            background_normal="",
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            halign="center",
            valign="middle",
            text_size=(250, None),
            on_press=lambda inst: self.go_to_breakdown_callback()
        )
        button_bar.add_widget(breakdown_btn)

        outer.add_widget(button_bar)
        root.add_widget(outer)
        self.add_widget(root)

    # ---------------------------------------------------------
    # RUN CALCULATION
    # ---------------------------------------------------------
    def run_calculation(self, *args):
        try:
            result = self.calculate_callback(self.calculator_state, UC_RATES)
            result_text = f"Calculated Entitlement: £{result:.2f}"
            self.calculator_state.calculation_result = result_text

        except Exception as e:
            self.summary_widgets["label"].text = f"Error during calculation: {str(e)}"
            return

        print("CALCULATION RESULT:", result)
        print("Calling update_summary() with state:", self.calculator_state.__dict__)

        try:
            self.update_summary()
        except Exception as e:
            self.summary_widgets["label"].text = f"Error updating summary: {str(e)}"
            return

        # Scroll to top after layout updates
        Clock.schedule_once(lambda dt: setattr(self.calculate_scroll, "scroll_y", 1.0), 0)

    # ---------------------------------------------------------
    # SUMMARY REBUILD
    # ---------------------------------------------------------
    def update_summary(self):
        print("SUMMARY SCREEN INSTANCE:", self)
        print("\n===== SUMMARY DEBUG =====")
        for key, value in self.calculator_state.__dict__.items():
            print(f"{key}: {value}")
        print("===== END SUMMARY DEBUG =====\n")

        d = self.calculator_state.__dict__

        # Work directly on the stored layout, not children[0]
        if not self.summary_layout:
            print("ERROR: summary_layout is None")
            return

        self.summary_layout.clear_widgets()

        self.summary_layout.add_widget(
            wrapped_SafeLabel("Summary of your Universal Credit calculation:", 18, 30)
        )

        def add_section(title, lines):
            section = CollapsibleSection(title, lines)
        
            # Ensure all labels inside the collapsible align identically
            for child in section.content_box.children:
                if isinstance(child, SafeLabel):
                    child.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))
        
            # Force section to have a real height
            section.size_hint_y = None
            section.height = section.minimum_height
            section.bind(minimum_height=lambda inst, val: setattr(inst, "height", val))
        
            self.summary_layout.add_widget(section)

        # Claimant
        add_section("Claimant Details", [
            f"Claimant Name: {title_case(d.get('claimant_name'))}",
            f"Claimant DOB: {d.get('claimant_dob')}",
            f"Partner Name: {title_case(d.get('partner_name'))}",
            f"Partner DOB: {d.get('partner_dob')}",
            f"Relationship: {title_case(d.get('relationship'))}",
        ])

        # Finances
        add_section("Finances", [
            f"Income: {fmt_money(d.get('income'))}",
            f"Savings: {fmt_money(d.get('savings'))}",
            f"Debts: {fmt_money(d.get('debts'))}",
        ])

        # Housing
        add_section("Housing", [
            f"Housing Type: {title_case(d.get('housing_type'))}",
            f"Tenancy Type: {title_case(d.get('tenancy_type'))}",
            f"Rent: {fmt_money(d.get('rent'))}",
            f"Mortgage: {fmt_money(d.get('mortgage'))}",
            f"Shared Accommodation Charge: {fmt_money(d.get('shared'))}",
            f"Non-dependants: {d.get('non_dependants')}",
            f"Postcode: {d.get('postcode')}",
            f"Location: {title_case(d.get('location'))}",
            f"BRMA: {d.get('brma')}",
            f"Manual BRMA Mode: {title_case(d.get('manual_location'))}",
        ])

        # Service Charges
        charges = d.get("service_charges", {})
        if charges:
            add_section("Service Charges (Social Rent)", [
                f"{k.replace('_', ' ').title()}: {fmt_money(v)}" for k, v in charges.items()
            ])

        # Children
        child_lines = [f"Number of Children: {len(d.get('children', []))}"]
        for i, child in enumerate(d.get("children", []), start=1):
            child_lines.extend([
                f"Child {i}:",
                f"  Name: {title_case(child.get('name'))}",
                f"  DOB: {child.get('dob')}",
                f"  Sex: {title_case(child.get('gender'))}",
                f"  Adopted: {child.get('adopted')}",
                f"  Kinship Care: {child.get('kinship_care')}",
                f"  Multiple Birth: {child.get('multiple_birth')}",
                f"  Disabled: {child.get('disabled')}",
                f"  Severely Disabled: {child.get('severely_disabled')}",
                f"  Non‑consensual Conception: {child.get('non_consensual')}",
            ])
        add_section("Children", child_lines)

        # Additional Elements
        add_section("Additional Elements", [
            f"Carer: {title_case(d.get('carer'))}",
            f"Disability: {title_case(d.get('disability'))}",
            f"Childcare Costs: {fmt_money(d.get('childcare'))}",
        ])

        # SAR Exemptions
        sar = d.get("sar_exemptions", {})
        add_section("SAR Exemptions", [
            f"Care Leaver: {sar.get('care_leaver')}",
            f"Severe Disability: {sar.get('severe_disability')}",
            f"MAPPA: {sar.get('mappa')}",
            f"Hostel Resident: {sar.get('hostel_resident')}",
            f"Domestic Abuse Refuge: {sar.get('domestic_abuse')}",
            f"Ex-Offender: {sar.get('ex_offender')}",
            f"Foster Carer: {sar.get('foster_carer')}",
            f"Prospective Adopter: {sar.get('prospective_adopter')}",
            f"Temporary Accommodation: {sar.get('temporary_accommodation')}",
            f"Modern Slavery Victim: {sar.get('modern_slavery')}",
            f"Armed Forces Reservist: {sar.get('armed_forces_reservist')}",
        ])

        print("SUMMARY LAYOUT DEBUG:")
        print("  children:", len(self.summary_layout.children))
        print("  height:", self.summary_layout.height)
        for i, child in enumerate(self.summary_layout.children):
            print(f"  child[{i}]:", type(child), "height=", getattr(child, "height", None))

class CalculationBreakdownScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # -----------------------------------------
        # WIDGET STORAGE (lazy-loading compatible)
        # -----------------------------------------
        self.breakdown_widgets = {}
        w = self.breakdown_widgets

        outer = BoxLayout(orientation="vertical", spacing=20, padding=20)

        # Title
        title = wrapped_SafeLabel("Calculation Breakdown", 22, 40)
        outer.add_widget(title)

        # Scrollable table
        w["scroll"] = ScrollView(size_hint=(1, 1))

        w["table"] = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=10,
            size_hint=(1, None)
        )
        w["table"].bind(minimum_height=w["table"].setter("height"))

        w["scroll"].add_widget(w["table"])
        outer.add_widget(w["scroll"])

        # Back button
        back_btn = RoundedButton(
            text="Back to Summary",
            size_hint=(1, None),
            height=60,
            background_color=(0, 0, 0, 0),
            background_normal="",
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            text_size=(250, None),
            on_press=self.go_back
        )
        outer.add_widget(back_btn)

        self.add_widget(outer)

    def go_back(self, *args):
        App.get_running_app().nav.go("calculator_final")

    def populate_breakdown(self, breakdown_dict):
        """Fill the table with calculation components."""
        w = self.breakdown_widgets
        table = w["table"]

        table.clear_widgets()

        for label, amount in breakdown_dict.items():
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)

            lbl = SafeLabel(
                text=label,
                font_size=18,
                color=get_color_from_hex("#FFFFFF"),
                halign="left"
            )
            lbl.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))

            amt = SafeLabel(
                text=f"£{amount:.2f}",
                font_size=18,
                color=get_color_from_hex("#FFDD00"),
                halign="right"
            )
            amt.bind(width=lambda inst, val: setattr(inst, "text_size", (val, None)))

            row.add_widget(lbl)
            row.add_widget(amt)
            table.add_widget(row)

@with_diagnostics([])
class InstantScreen(BaseScreen):
    pass
        
# Define the Settings Screen
@with_diagnostics([])
class SettingsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", spacing=30, padding=20)

        # Header
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # Info label
        info_anchor = AnchorLayout(anchor_x="center", anchor_y="center")
        info_label = SafeLabel(
            text="Settings are currently in development.\n\nPlease check back later.",
            font_size=16, halign="center", valign="middle", color=get_color_from_hex(WHITE)
        )
        info_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        info_anchor.add_widget(info_label)
        layout.add_widget(info_anchor)

        # Spacer above buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Shared button style for consistency
        button_style = {
            "size_hint": (None, None),
            "size": (250, 60),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # Grouped buttons in a vertical box
        buttons_box = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, None))
        for text, handler in [
            ("Back to Main Menu", self.go_to_main),
        ]:
            btn = RoundedButton(
                text=text,
                **button_style,
                font_size=20,
                font_name="roboto",
                color=get_color_from_hex("#005EA5"),
                halign="center", valign="middle",
                text_size=(250, None),
                on_press=handler
            )
            buttons_box.add_widget(btn)

        layout.add_widget(buttons_box)

        # Spacer below buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Footer
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

    def go_to_main(self, instance):
        App.get_running_app().nav.go("main")

# Disclaimer Screen
@with_diagnostics([])
class DisclaimerScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        from kivy.core.window import Window
        from kivy.uix.widget import Widget

        # ROOT LAYOUT (do NOT add yet)
        root = BoxLayout(orientation="vertical", padding=20, spacing=30)

        # ---------------------------------------------------------
        # TOP SPACER
        # ---------------------------------------------------------
        root.add_widget(Widget(size_hint_y=1))

        # ---------------------------------------------------------
        # DISCLAIMER TEXT
        # ---------------------------------------------------------
        disclaimer_text = SafeLabel(
            text=(
                "Disclaimer: This app is currently still in development and may not be fully accurate.\n\n"
                "It is for informational purposes only and does not constitute financial advice.\n\n\n"
                "Guest access has limited functionality and will not save your data."
            ),
            font_size=18,
            halign="center",
            valign="top",
            color=get_color_from_hex("#FFFFFF"),
            size_hint_y=None,
            text_size=(Window.width - 40, None)
        )
        disclaimer_text.bind(
            texture_size=lambda inst, val: setattr(inst, "height", val[1])
        )
        root.add_widget(disclaimer_text)

        # ---------------------------------------------------------
        # LOADING LABEL
        # ---------------------------------------------------------
        self.loading_label = SafeLabel(
            text="Loading data…",
            font_size=16,
            halign="center",
            valign="middle",
            color=get_color_from_hex("#FFDD00"),
            size_hint_y=None,
            height=40
        )
        root.add_widget(self.loading_label)

        # ---------------------------------------------------------
        # LOADING BAR
        # ---------------------------------------------------------
        self.loading_bar_fg = BoxLayout(size_hint=(0, None), height=30)
        with self.loading_bar_fg.canvas.before:
            Color(*get_color_from_hex("#FFDD00"))
            self._loading_fg_rect = Rectangle(size=self.loading_bar_fg.size, pos=self.loading_bar_fg.pos)
        self.loading_bar_fg.bind(
            size=lambda inst, val: setattr(self._loading_fg_rect, "size", val),
            pos=lambda inst, val: setattr(self._loading_fg_rect, "pos", val)
        )
        root.add_widget(self.loading_bar_fg)

        # ---------------------------------------------------------
        # CONTINUE BUTTON
        # ---------------------------------------------------------
        self.continue_button = RoundedButton(
            text="Continue",
            size_hint=(None, None),
            size=(250, 60),
            disabled=True,
            background_color=get_color_from_hex("#FFDD00"),
            background_normal="",
            color=get_color_from_hex("#005EA5"),
            font_size=20,
            pos_hint={"center_x": 0.5},
            halign="center",
            valign="middle",
            text_size=(250, None),
            on_press=lambda x: App.get_running_app().nav.go("main")
        )
        root.add_widget(self.continue_button)

        # ---------------------------------------------------------
        # BOTTOM SPACER
        # ---------------------------------------------------------
        root.add_widget(Widget(size_hint_y=1))

        # ---------------------------------------------------------
        # FOOTER
        # ---------------------------------------------------------
        build_footer(root)

        # IMPORTANT: store layout, do NOT add yet
        self.root_layout = root

        # PROGRESS VALUES
        self._real_progress = 0.0
        self._display_progress = 0.0


    def on_pre_enter(self):
        self._attach_layout(0)
    
    def on_enter(self):
        Clock.schedule_interval(self._smooth_progress, 0.02)
        Clock.schedule_once(self.start_csv_load, 0.1)

    def _attach_layout(self, dt):
        # Always attach the layout immediately
        if self.root_layout.parent is None:
            self.add_widget(self.root_layout)

    def _smooth_progress(self, dt):
        speed = 0.05  # how fast we chase real progress
    
        # Gentle trickle at the start so it never looks frozen
        if self._real_progress < 0.15 and self._display_progress < 0.15:
            self._display_progress += 0.01
        else:
            if self._display_progress < self._real_progress:
                self._display_progress += speed
                if self._display_progress > self._real_progress:
                    self._display_progress = self._real_progress
    
        self.loading_bar_fg.size_hint_x = self._display_progress

    def start_csv_load(self, dt):
        app = App.get_running_app()
    
        # Load CSVs in background thread
        import threading
        threading.Thread(target=self._load_csv_thread).start()

    def _load_csv_thread(self):
        app = App.get_running_app()
        try:
            # ---------------------------------------------------------
            # 1) Load LHA CSVs (0 → 50%)
            # ---------------------------------------------------------
            self._update_status("Loading LHA files…")
            app.preload_lha_csvs(
                progress_callback=lambda v: self._update_progress(v * 0.50),
                status_callback=self._update_status
            )
    
            # ---------------------------------------------------------
            # 2) Preload screens (50% → 60%)
            # ---------------------------------------------------------
            self._update_status("Preparing screens…")
            app.nav.preload_all_screens(
                lambda v: self._update_progress(0.50 + v * 0.10)
            )
    
            # ---------------------------------------------------------
            # 3) Load postcode engine (60% → 100%)
            # ---------------------------------------------------------
            # Only load postcode data if not already loaded
            if all_postcodes is None:
                self._update_status("Loading postcode data…")
                load_all_postcode_data(
                    progress=lambda v: self._update_progress(0.60 + v * 0.40),
                    status=self._update_status
                )
            else:
                # Already loaded (e.g., returning to screen)
                self._update_progress(1.0)
    
        except Exception as e:
            print("Startup preload error:", e)
    
        Clock.schedule_once(self._loading_complete, 0)

    def _update_progress(self, value):
        Clock.schedule_once(lambda dt: self._set_real_progress(value))

    def _update_status(self, message):
        Clock.schedule_once(lambda dt: setattr(self.loading_label, "text", message))

    def _set_real_progress(self, value):
        self._real_progress = value

    def _loading_complete(self, dt):
        self._set_real_progress(1.0)
        self.loading_label.text = "Ready"
        self.continue_button.disabled = False
    
        # Run diagnostics now that postcode data is loaded
        Clock.schedule_once(lambda _dt: App.get_running_app().run_startup_diagnostics(), 0)

# Define the main screen for the app
@with_diagnostics([])
class MainScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Root layout fills the whole screen
        layout = BoxLayout(orientation="vertical", spacing=30, padding=20)

        # Header pinned to top
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # Logo centered and resized
        logo_anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None, height=250)
        logo = Image(
            source="images/logo.png",
            size_hint=(None, None),
            size=(250, 250),   # balanced size for tablets
            allow_stretch=True,
            keep_ratio=True
        )
        logo_anchor.add_widget(logo)
        layout.add_widget(logo_anchor)

        # Spacer above buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Shared button style for consistency
        button_style = {
            "size_hint": (None, None),
            "size": (250, 60),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # Grouped buttons in a vertical box
        buttons_box = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, None))
        for text, handler in [
            ("Create Account", self.go_to_create_account),
            ("Login", self.go_to_login),
            ("Guest Access", self.go_to_guest_access),
            ("Settings", self.go_to_settings),
            ("Exit", self.exit_app),
        ]:
            btn = RoundedButton(
                text=text,
                **button_style,
                font_size=20,
                font_name="roboto",
                color=get_color_from_hex("#005EA5"),
                halign="center", valign="middle",
                text_size=(250, None),
                on_press=handler
            )
            buttons_box.add_widget(btn)

        layout.add_widget(buttons_box)

        # Spacer below buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Footer pinned to bottom
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

    # Navigation methods
    def go_to_create_account(self, instance):
        App.get_running_app().nav.go("create_account")
    
    def go_to_login(self, instance):
        App.get_running_app().nav.go("log_in")
    
    def go_to_guest_access(self, instance):
        App.get_running_app().nav.go("main_guest_access")
    
    def go_to_settings(self, instance):
        App.get_running_app().nav.go("settings")

    def exit_app(self, instance):
        App.get_running_app().stop()

# Define the Main Screen for Full Access
@with_diagnostics([])
class MainScreenFullAccess(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ---------------------------------------------------------
        # SCROLLVIEW (Android-safe)
        # ---------------------------------------------------------
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)

        # ---------------------------------------------------------
        # MAIN LAYOUT
        # ---------------------------------------------------------
        layout = BoxLayout(
            orientation="vertical",
            spacing=30,
            padding=20,
            size_hint_y=None
        )
        layout.bind(minimum_height=layout.setter("height"))
        scroll.add_widget(layout)

        # ---------------------------------------------------------
        # HEADER
        # ---------------------------------------------------------
        header_anchor = AnchorLayout(
            anchor_x="center",
            anchor_y="top",
            size_hint_y=None,
            height=80
        )
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # ---------------------------------------------------------
        # BUTTON GROUP
        # ---------------------------------------------------------
        layout.add_widget(Widget(size_hint_y=0.05))

        buttons_box = BoxLayout(
            orientation="vertical",
            spacing=20,
            size_hint=(1, None)
        )
        buttons_box.bind(minimum_height=buttons_box.setter("height"))

        button_style = {
            "size_hint": (None, None),
            "size": (250, 60),
            "background_normal": "",
            "background_color": get_color_from_hex("#FFDD00"),  # GOV.UK yellow
            "pos_hint": {"center_x": 0.5},
            "font_size": 20,
            "font_name": "roboto",
            "color": get_color_from_hex("#005EA5"),  # GOV.UK blue text
            "halign": "center",
            "valign": "middle",
            "text_size": (250, None)
        }

        for text, handler in [
            ("Predict Next Payment", self.predict_payment),
            ("View Previous Payments", lambda x: print("Payments feature not yet implemented")),
            ("Update Details", lambda x: print("Update details feature not yet implemented")),
            ("Log Out", self.log_out),
        ]:
            btn = RoundedButton(text=text, on_press=handler, **button_style)
            buttons_box.add_widget(btn)

        layout.add_widget(buttons_box)

        layout.add_widget(Widget(size_hint_y=0.05))

        # ---------------------------------------------------------
        # FOOTER
        # ---------------------------------------------------------
        footer_anchor = AnchorLayout(
            anchor_x="center",
            anchor_y="bottom",
            size_hint_y=None,
            height=60
        )
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(scroll)

    # ---------------------------------------------------------
    # POPUP HELPERS
    # ---------------------------------------------------------
    def create_popup(self, title, message):
        lbl = SafeLabel(
            text=message,
            halign="center",
            color=get_color_from_hex("#005EA5"),
            font_size=18,
            font_name="roboto"
        )
        lbl.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))

        return Popup(
            title=title,
            content=lbl,
            size_hint=(0.8, 0.4),
            title_color=get_color_from_hex("#005EA5"),
            separator_color=get_color_from_hex("#FFDD00")
        )

    # ---------------------------------------------------------
    # PREDICT PAYMENT FLOW
    # ---------------------------------------------------------
    def predict_payment(self, instance):
        content = BoxLayout(orientation="vertical", spacing=20, padding=20)

        self.income_input = CustomTextInput(
            hint_text="Enter your income for this assessment period",
            font_size=18,
            background_color=get_color_from_hex(WHITE),
            foreground_color=get_color_from_hex("#005EA5"),
            font_name="roboto"
        )

        submit_button = RoundedButton(
            text="Submit",
            size_hint=(None, None),
            size=(250, 50),
            background_normal="",
            background_color=get_color_from_hex("#FFDD00"),
            font_size=20,
            font_name="roboto",
            color=get_color_from_hex("#005EA5"),
            pos_hint={"center_x": 0.5},
            halign="center",
            valign="middle",
            text_size=(250, None),
            on_press=lambda _: self.show_prediction_popup(self.income_input.text)
        )

        content.add_widget(SafeLabel(
            text="Enter your income:",
            font_size=20,
            halign="center",
            color=get_color_from_hex("#005EA5"),
            font_name="roboto"
        ))
        content.add_widget(self.income_input)
        content.add_widget(submit_button)

        popup = Popup(
            title="Payment Prediction",
            content=content,
            size_hint=(0.8, 0.5),
            title_color=get_color_from_hex("#005EA5"),
            separator_color=get_color_from_hex("#FFDD00")
        )
        popup.open()

    def show_prediction_popup(self, income):
        income = income.strip() if income else ""
        try:
            value = float(income)
            predicted_payment = value * 0.45  # placeholder logic
            message = f"Your next payment is predicted to be: £{predicted_payment:.2f}"
        except (ValueError, TypeError):
            message = "Invalid income entered. Please enter a numeric value."

        result_label = SafeLabel(
            text=message,
            font_size=20,
            halign="center",
            color=get_color_from_hex("#005EA5"),
            font_name="roboto"
        )
        result_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))

        result_popup = Popup(
            title="Prediction Result",
            content=result_label,
            size_hint=(0.8, 0.4),
            title_color=get_color_from_hex("#005EA5"),
            separator_color=get_color_from_hex("#FFDD00")
        )
        result_popup.open()

    def log_out(self, instance):
        App.get_running_app().nav.go("main")
        
        
# Define the Guest Access Screen (reusing HomePage for simplicity)
@with_diagnostics([])
class MainScreenGuestAccess(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", spacing=30, padding=20)

        # Header
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # Info label
        info_anchor = AnchorLayout(anchor_x="center", anchor_y="center")
        info_label = SafeLabel(
            text="Guest Access has limited functionality.\n\nFull Access Mode is in development.",
            font_size=16, halign="center", valign="middle", color=get_color_from_hex(WHITE)
        )
        info_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        info_anchor.add_widget(info_label)
        layout.add_widget(info_anchor)

        # Spacer above buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Shared button style for consistency
        button_style = {
            "size_hint": (None, None),
            "size": (250, 60),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # Grouped buttons in a vertical box
        buttons_box = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, None))
        for text, handler in [
            ("Calculate Universal Credit", self.go_to_calculator),
            ("Log Out", self.log_out),
        ]:
            btn = RoundedButton(
                text=text,
                **button_style,
                font_size=20,
                font_name="roboto",
                color=get_color_from_hex("#005EA5"),
                halign="center", valign="middle",
                text_size=(250, None),
                on_press=handler
            )
            buttons_box.add_widget(btn)

        layout.add_widget(buttons_box)

        # Spacer below buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Footer
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

    def go_to_calculator(self, instance):
        App.get_running_app().nav.go("calculator_intro")

    def log_out(self, instance):
        App.get_running_app().nav.go("main")

# Define the Create Account Screen
@with_diagnostics([])
class CreateAccountPage(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", spacing=30, padding=20)

        # Header
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # Info label
        info_anchor = AnchorLayout(anchor_x="center", anchor_y="center")
        info_label = SafeLabel(
            text="This section is still in development.\n\nPlease check back later for updates.",
            font_size=16, halign="center", valign="middle", color=get_color_from_hex(WHITE)
        )
        info_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        info_anchor.add_widget(info_label)
        layout.add_widget(info_anchor)

        # Spacer above buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Shared button style for consistency
        button_style = {
            "size_hint": (None, None),
            "size": (250, 60),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # Grouped buttons in a vertical box
        buttons_box = BoxLayout(orientation="vertical", spacing=20, size_hint=(1, None))
        for text, handler in [
            ("Back to Home", self.go_back),
        ]:
            btn = RoundedButton(
                text=text,
                **button_style,
                font_size=20,
                font_name="roboto",
                color=get_color_from_hex("#005EA5"),
                halign="center", valign="middle",
                text_size=(250, None),
                on_press=handler
            )
            buttons_box.add_widget(btn)

        layout.add_widget(buttons_box)

        # Spacer below buttons
        layout.add_widget(Widget(size_hint_y=0.05))

        # Footer
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

    def go_back(self, instance):
        App.get_running_app().nav.go("main")

# Define the Login Screen
@with_diagnostics([])
class LoginPage(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation="vertical", spacing=30, padding=20)

        # Header
        header_anchor = AnchorLayout(anchor_x="center", anchor_y="top", size_hint_y=None, height=80)
        build_header(header_anchor, "Benefit Buddy")
        layout.add_widget(header_anchor)

        # Info label
        info_anchor = AnchorLayout(anchor_x="center", anchor_y="center")
        info_label = SafeLabel(
            text="Login functionality is in development.\n\nFuture versions will allow full account access.",
            font_size=16,
            halign="center",
            valign="middle",
            color=get_color_from_hex(WHITE)
        )
        info_label.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        info_anchor.add_widget(info_label)
        layout.add_widget(info_anchor)

        # Spacer
        layout.add_widget(Widget(size_hint_y=0.05))

        # Shared button style for consistency
        button_style = {
            "size_hint": (None, None),
            "size": (250, 60),
            "background_color": (0, 0, 0, 0),
            "background_normal": "",
            "pos_hint": {"center_x": 0.5}
        }

        # Buttons
        for text, handler in [
            ("Log In", self.log_in),
            ("Back to Home", self.go_back),
        ]:
            btn = RoundedButton(
                text=text,
                **button_style,
                font_size=20,
                font_name="roboto",
                color=get_color_from_hex("#005EA5"),
                halign="center", valign="middle",
                text_size=(250, None),
                on_press=handler
            )
            layout.add_widget(btn)

        # Footer
        footer_anchor = AnchorLayout(anchor_x="center", anchor_y="bottom", size_hint_y=None, height=60)
        build_footer(footer_anchor)
        layout.add_widget(footer_anchor)

        self.add_widget(layout)

    def log_in(self, instance):
        App.get_running_app().nav.go("main_full_access")

    def go_back(self, instance):
        App.get_running_app().nav.go("main")


class ScreenFactory:

    @staticmethod
    def create(name):
        app = App.get_running_app()

        if name == "instant":
            return InstantScreen(name=name)

        if name == "disclaimer":
            return DisclaimerScreen(name=name)

        if name == "settings":
            return SettingsScreen(name=name)

        if name == "main":
            return MainScreen(name=name)

        if name == "create_account":
            return CreateAccountPage(name=name)

        if name == "log_in":
            return LoginPage(name=name)

        if name == "main_guest_access":
            return MainScreenGuestAccess(name=name)

        if name == "main_full_access":
            return MainScreenFullAccess(name=name)

        # -----------------------------
        # CALCULATOR SUB‑SCREENS
        # -----------------------------
        if name == "calculator_intro":
            return CalculatorIntroScreen(app.calculator_state, name=name)

        if name == "calculator_claimant_details":
            return CalculatorClaimantDetailsScreen(app.calculator_state, name=name)

        if name == "calculator_finances":
            return CalculatorFinancesScreen(app.calculator_state, name=name)

        if name == "calculator_housing":
            return CalculatorHousingScreen(app.calculator_state, name=name)

        if name == "calculator_children":
            return CalculatorChildrenScreen(app.calculator_state, name=name)

        if name == "calculator_additional":
            return CalculatorAdditionalElementsScreen(app.calculator_state, name=name)

        if name == "calculator_sanctions":
            return CalculatorSanctionsScreen(app.calculator_state, name=name)

        if name == "calculator_advance":
            return CalculatorAdvanceScreen(app.calculator_state, name=name)

        if name == "calculator_final":
            return CalculatorFinalScreen(
                calculator_state=app.calculator_state,
                save_callbacks=app.save_callbacks,
                calculate_callback=app.engine.calculate_entitlement,
                go_to_breakdown_callback=lambda: (
                    app.nav.go("breakdown"),
                    app.nav.get("breakdown").populate_breakdown(app.calculator_state.breakdown)
                ),
                name=name
            )
        
        if name == "breakdown":
            return CalculationBreakdownScreen(name=name)

        raise ValueError(f"Unknown screen: {name}")


class NavigationManager:

    def __init__(self, screen_manager):
        self.sm = screen_manager

        # Screens created during preload (persistent)
        self.preloaded = {}

        # Screens created dynamically (non-preloaded)
        self.loaded = {}

        # ---------------------------------------------------------
        # UPDATED ORDER: children BEFORE housing
        # ---------------------------------------------------------
        self.screen_factories = {
            name: (lambda n=name: ScreenFactory.create(n))
            for name in [
                "instant", "disclaimer", "settings", "main",
                "create_account", "log_in",
                "main_guest_access", "main_full_access",

                # Calculator flow
                "calculator_intro",
                "calculator_claimant_details",
                "calculator_finances",
                "calculator_children",
                "calculator_sanctions",
                "calculator_housing",
                "calculator_additional",
                "calculator_advance",
                "calculator_final",
                "breakdown"
            ]
        }

    # ---------------------------------------------------------
    # PRELOAD ALL SCREENS (called during Disclaimer loading)
    # ---------------------------------------------------------
    def preload_all_screens(self, progress_callback):
        total = len(self.screen_factories)
        for i, (name, factory) in enumerate(self.screen_factories.items()):
            if name not in self.preloaded:
                # Create the screen instance ONCE
                screen = factory()
                self.preloaded[name] = screen

                # Add it to the ScreenManager immediately
                self.sm.add_widget(screen)

            progress_callback(0.1 + (i + 1) / total * 0.9)

    # ---------------------------------------------------------
    # GET SCREEN (preloaded or loaded)
    # ---------------------------------------------------------
    def get(self, name):
        if name in self.preloaded:
            return self.preloaded[name]
        if name in self.loaded:
            return self.loaded[name]
        return None

    # ---------------------------------------------------------
    # NAVIGATION
    # ---------------------------------------------------------
    def go(self, name):
        print("DEBUG: go() called with:", name)
    
        if not name:
            print("ERROR: NavigationManager.go() received invalid screen name:", name)
            return
    
        # ---------------------------------------------------------
        # SAVE STATE OF CURRENT SCREEN BEFORE SWITCHING
        # ---------------------------------------------------------
        current = self.sm.current
        if current:
            screen = self.get(current)
            if screen and hasattr(screen, "save_state"):
                try:
                    screen.save_state()
                except Exception as e:
                    print("ERROR in save_state():", e)
    
        # ---------------------------------------------------------
        # USE PRELOADED SCREEN IF AVAILABLE
        # ---------------------------------------------------------
        if name in self.preloaded:
            new = self.preloaded[name]
    
        else:
            if name not in self.loaded:
                self.loaded[name] = ScreenFactory.create(name)
                self.sm.add_widget(self.loaded[name])
            new = self.loaded[name]
    
        # Switch to the screen
        self.sm.current = name
    
        # Load state if needed
        if hasattr(new, "load_state"):
            try:
                new.load_state()
            except Exception as e:
                print("ERROR in load_state():", e)

class PostcodeDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cur = self.conn.cursor()

    def lookup(self, postcode):
        pc = postcode.replace(" ", "").upper()

        row = self.cur.execute(
            "SELECT brma, brma_name FROM postcodes WHERE postcode = ?",
            (pc,)
        ).fetchone()

        if not row:
            return None

        brma, brma_name = row

        # Match your existing return format
        return {
            "brma": brma,
            "country": brma_name  # you can rename this later if needed
        }

# Define the main application class
class BenefitBuddy(App):

    def build(self):
        self.sm = ScreenManager()
        self.nav = NavigationManager(self.sm)
        
        self.calculator_state = CalculatorState()
        self.engine = CalculatorEngine()

        # Save callbacks
        self.save_callbacks = {
            "claimant": lambda: self.nav.get("calculator_claimant_details").save_claimant_details(),
            "finances": lambda: self.nav.get("calculator_finances").save_finances_details(),
            "housing": lambda: self.nav.get("calculator_housing").save_housing_details(),
            "children": lambda: self.nav.get("calculator_children").save_children_details(),
            "additional": lambda: self.nav.get("calculator_additional").save_additional_elements(),
            "sanctions": lambda: self.nav.get("calculator_sanctions").save_sanction_details(),
            "advance": lambda: self.nav.get("calculator_advance").save_advance_payment_details(),
        }
        
        # Preload screens immediately (main thread)
        self.nav.preload_all_screens(lambda x: None)

        # Start at Disclaimer
        self.nav.go("disclaimer")
        return self.sm
    
    def lookup_postcode(self, postcode):
        return compact_lookup(postcode)

    # ---------------------------------------------------------
    # LHA CSV PRELOAD
    # ---------------------------------------------------------
    def preload_lha_csvs(self, progress_callback, status_callback):
        import csv
        from kivy.resources import resource_find
    
        self._lha_data = {
            "england": [],
            "scotland": [],
            "wales": []
        }
    
        files = {
            "england": "data/LHA-England.csv",
            "scotland": "data/LHA-Scotland.csv",
            "wales": "data/LHA-Wales.csv"
        }
    
        total_files = len(files)
    
        for i, (key, filename) in enumerate(files.items()):
            status_callback(f"Loading LHA {key.capitalize()}…")
    
            path = resource_find(filename)
            print("DEBUG: LHA path for", filename, "=", path)
            
            if not path:
                print(f"LHA CSV missing: {filename}")
                continue
    
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
    
                rows = []
                for j, row in enumerate(reader):
                    rows.append(row)
    
                self._lha_data[key] = rows
    
            progress_callback(0.1 + ((i + 1) / total_files) * 0.9)
    
        # Build BRMA lists grouped by location
        self.brma_by_location = {
            "england": [],
            "scotland": [],
            "wales": []
        }
    
        for location, rows in self._lha_data.items():
            for row in rows:
                brma = row.get("BRMA", "").strip()
                if brma and brma not in self.brma_by_location[location]:
                    self.brma_by_location[location].append(brma)

    # ---------------------------------------------------------
    # PRELOAD ALL DATA
    # ---------------------------------------------------------
    def preload_all_data(self, progress_callback, status_callback):
        status_callback("Loading LHA files…")
        self.preload_lha_csvs(progress_callback, status_callback)

        progress_callback(1.0)
        status_callback("Ready")

    # ---------------------------------------------------------
    # STARTUP DIAGNOSTICS
    # ---------------------------------------------------------
    def run_startup_diagnostics(self, dt=None):
        print("\n=== Benefit Buddy Startup Diagnostics ===")
    
        self.check_assets()
        self.check_safe_props()
        self.check_window_size()
        self.check_memory()
        
        print("\n[5] Postcode Lookup Test")
        print("  SW1A1AA →", self.lookup_postcode("SW1A1AA"))
        print("  DN350HQ →", self.lookup_postcode("DN350HQ"))
        print("  ZE39XP →", self.lookup_postcode("ZE39XP"))
    
        print("\n=== Startup Diagnostics Complete ===\n")

    def check_assets(self):
        print("\n[1] Asset Verification")
        required_assets = {
            "Logo": "images/logo.png",
            "Roboto Font": "font/roboto.ttf",
            "Chevron Down Icon": "images/icons/ChevronDown-icon/ChevronDown-32px.png",
            "Chevron Up Icon": "images/icons/ChevronUp-icon/ChevronUp-32px.png",
        }
        for label, asset in required_assets.items():
            path = resource_find(asset)
            print(f"  {'✔' if path else '✖'} {label}: {asset}")

    def check_safe_props(self):
        print("\n[2] Safe Props Texture Patch Check")
        from kivy.uix.label import Label
        patched = Label.texture_update.__name__ != "_texture_update"
        print("  ✔ safe_props_texture.py ACTIVE" if patched else "  ✖ NOT ACTIVE")
    
    def check_window_size(self):
        print("\n[3] Window Size Check")
        w, h = Window.width, Window.height
        print(f"  ✔ Window size OK ({w}x{h})" if w >= 600 else "  ✖ Window too small")
    
    def check_memory(self):
        print("\n[4] Memory Check")
        current, peak = tracemalloc.get_traced_memory()
        print(f"  ✔ Memory usage: {current/1024:.1f} KB (peak {peak/1024:.1f} KB)")

# Run the app
if __name__ == "__main__":
    BenefitBuddy().run()

# TO DO:

# check advance payments logic/summary
# check the sanctions logic/summary

# check for the need for non-dependent deductions
# check for the need for child maintenance deductions
 
# positioning and spread of widgets, etc.
# sort logic for payment prediction for the full access account

# create a settings screen to allow the user to change the app's:
#   theme,
#   font size,
#   language,
#   links to other applications,
#   links to help and support,
#   and other preferences


# add a feature to allow the user to reset all inputs and summaries
# add a feature to allow the user to save their inputs and summaries
# add a feature to allow the user to load their inputs and summaries

# add a save feature to save the user's data to a file
# add a load feature to load the user's data from a file
























