# uc_calculator.py


# Constants for standard allowances based on age and relationship status
STANDARD_ALLOWANCE_SINGLE_UNDER_25 = 316.98
STANDARD_ALLOWANCE_SINGLE_25_AND_OVER = 400.14
STANDARD_ALLOWANCE_COUPLE_UNDER_25 = 497.55
STANDARD_ALLOWANCE_COUPLE_25_AND_OVER = 628.10

# Constants for child elements based on the year of birth and disability status
CHILD_ELEMENT_BORN_BEFORE_2017 = 339
CHILD_ELEMENT_BORN_AFTER_2017 = 292.81
CHILD_ELEMENT_DISABLED_HIGH_RATE = 495.87
CHILD_ELEMENT_DISABLED_LOW_RATE = 158.76

# Constants for work capability elements
WORK_CAPABILITY_LCW = 158.76
WORK_CAPABILITY_LCWRA = 423.27

# Constants for carer element
CARER_ELEMENT = 201.68

# Constants for childcare costs
CHILDCARE_COSTS_ONE_CHILD = 1031.88
CHILDCARE_COSTS_TWO_OR_MORE_CHILDREN = 1768.94

# Constants for capital income calculation
CAPITAL_INCOME_LOWER_LIMIT = 6000
CAPITAL_INCOME_UPPER_LIMIT = 16000
CAPITAL_INCOME_RATE = 4.35

# Constants for capital income calculation blocks
CAPITAL_INCOME_BLOCK_SIZE = 250
CAPITAL_INCOME_BLOCKS = 249  # Rounding up each 250

# Constants for work allowance based on children and housing support
WORK_ALLOWANCE_CHILDREN = 411
WORK_ALLOWANCE_NO_CHILDREN = 684

# Constants for housing element calculation
HOUSING_ELEMENT_MAX_ONE_CHILD = 1031.88
HOUSING_ELEMENT_MAX_TWO_OR_MORE_CHILDREN = 1768.94

# Constants for non-dependant deductions
NON_DEPENDANT_DEDUCTION = 93.02

# Constants for maximum deductions based on age and relationship status
MAX_DEDUCTION_SINGLE_UNDER_25 = 47.55
MAX_DEDUCTION_SINGLE_25_AND_OVER = 60.02
MAX_DEDUCTION_COUPLE_UNDER_25 = 74.63
MAX_DEDUCTION_COUPLE_25_AND_OVER = 94.22

# Constants for minimum UC amount
MIN_UC_AMOUNT = 0.01

# Constants for maximum UC amount
MAX_UC_AMOUNT = 0.00  # Capital above £16,000 makes claimant ineligible

# Constants for earnings tapering rate
EARNINGS_TAPER_RATE = 0.55

# Constants for earnings tapering allowance based on children and LCW
EARNINGS_TAPER_ALLOWANCE_CHILDREN = 411
EARNINGS_TAPER_ALLOWANCE_NO_CHILDREN = 684



# Function to calculate the standard allowance based on age and relationship status
def get_standard_allowance(age, is_single=True, partner_age=None):
    if is_single:
        return 316.98 if age < 25 else 400.14
    else:
        if age < 25 and partner_age is not None and partner_age < 25:
            return 497.55
        else:
            return 628.10

# Function to calculate the child elements based on the number of children and their attributes
def get_child_elements(children):
    amount = 0
    for child in children:
        if child['born_before_2017']:
            amount += 339
        else:
            amount += 292.81
        if child['disabled']:
            amount += 495.87 if child['high_rate'] else 158.76
    return amount

# Function to calculate the work capability element based on LCW and LCWRA status
def get_work_capability(lcw=False, lcwra=False, lcw_since_before_apr_2017=False):
    if lcwra:
        return 423.27
    elif lcw and lcw_since_before_apr_2017:
        return 158.76
    return 0

# Function to calculate the carer element based on carer status
def get_carer_element(is_carer):
    return 201.68 if is_carer else 0

# Function to calculate the childcare costs based on the number of children and actual costs
def get_childcare_costs(num_children, actual_costs):
    max_allowed = 1031.88 if num_children == 1 else 1768.94
    return min(actual_costs, max_allowed)

# Function to calculate the capital income based on the capital amount
def calculate_capital_income(capital):
    if capital <= 6000:
        return 0
    elif capital >= 16000:
        return float('inf')  # not eligible
    else:
        blocks = ((capital - 6000) + 249) // 250
        return blocks * 4.35

# Function to calculate the work allowance based on children and housing support
def get_work_allowance(has_children_or_lcw, receives_housing_support):
    if has_children_or_lcw:
        return 411 if receives_housing_support else 684
    return 0

# Function to calculate the earnings taper based on earnings, children, and housing support
def calculate_earnings_taper(earnings, has_children_or_lcw, receives_housing_support):
    allowance = get_work_allowance(has_children_or_lcw, receives_housing_support)
    excess = max(0, earnings - allowance)
    taper_deduction = 0.55 * excess
    return taper_deduction

# Function to calculate the housing element based on eligible rent and non-dependant deductions
def calculate_housing_element(eligible_rent, num_non_dependants=0):
    non_dep_deduction = num_non_dependants * 93.02
    housing_support = max(0, eligible_rent - non_dep_deduction)
    return housing_support

# Function to apply deductions to the UC amount based on age and relationship status
def apply_deductions(uc_amount, deductions, is_single, age, is_joint=False, partner_age=None):
    if is_single:
        max_deduction = 60.02 if age >= 25 else 47.55
    else:
        if age >= 25 or (partner_age and partner_age >= 25):
            max_deduction = 94.22
        else:
            max_deduction = 74.63
    total_deductions = min(sum(deductions), max_deduction)
    return max(0.01, uc_amount - total_deductions)

# Function to calculate the total UC amount based on all elements and deductions
def calculate_uc_eligibility(claimant):
    
    # Calculate the standard allowance based on age and relationship status
    standard_allowance = get_standard_allowance(claimant['age'], claimant['is_single'], claimant.get('partner_age'))

    # Calculate the child elements based on the number of children and their attributes
    child_elements = get_child_elements(claimant['children'])

    # Calculate the work capability element based on LCW and LCWRA status
    work_capability = get_work_capability(claimant.get('lcw', False), claimant.get('lcwra', False))

    # Calculate the carer element based on carer status
    carer_element = get_carer_element(claimant.get('is_carer', False))

    # Calculate the childcare costs based on the number of children and actual costs
    childcare_costs = get_childcare_costs(len(claimant['children']), claimant.get('childcare_costs', 0))

    # Calculate the capital income based on the capital amount
    capital_income = calculate_capital_income(claimant.get('capital', 0))

    # Check if capital income makes claimant ineligible
    if capital_income == float('inf'):
        return 0.00  # Capital above £16,000 makes claimant ineligible

    # Calculate the work allowance based on children and housing support
    work_allowance = get_work_allowance(len(claimant['children']) > 0 or claimant.get('lcw', False), claimant.get('receives_housing_support', False))

    # Calculate the earnings taper based on earnings, children, and housing support
    earnings_taper = calculate_earnings_taper(claimant.get('earnings', 0), len(claimant['children']) > 0 or claimant.get('lcw', False), claimant.get('receives_housing_support', False))

    # Calculate the housing element based on eligible rent and non-dependant deductions
    housing_element = calculate_housing_element(claimant.get('eligible_rent', 0), claimant.get('non_dependants', 0))

    # Sum all elements to get the total UC amount before deductions
    total_uc_before_deductions = (standard_allowance + child_elements + work_capability +
                                  carer_element + childcare_costs + housing_element - earnings_taper)

    # Apply deductions to the UC amount based on age and relationship status
    final_uc_amount = apply_deductions(total_uc_before_deductions, [capital_income], claimant['is_single'], claimant['age'],
                                        claimant.get('is_joint', False), claimant.get('partner_age'))
    
    
    # Return the final UC amount after all calculations
    return final_uc_amount

# Interactive calculator function
def uc_calculator():
    # Welcome message and instructions
    print("Universal Credit Calculator")
    print("Welcome to the Universal Credit Calculator!")
    print("Please provide the following information:")

    # Collect claimant information
    age = int(input("Enter your age: "))
    is_single = input("Are you single? (yes/no): ").strip().lower() == 'yes'
    partner_age = int(input("Enter your partner's age (if applicable, otherwise enter 0): ")) if not is_single else None
    num_children = int(input("Enter the number of children: "))
    children = []
    for i in range(num_children):
        print(f"Enter details for child {i + 1}:")
        born_before_2017 = input("Was the child born before 2017? (yes/no): ").strip().lower() == 'yes'
        disabled = input("Is the child disabled? (yes/no): ").strip().lower() == 'yes'
        high_rate = input("Does the child receive the high rate disability payment? (yes/no): ").strip().lower() == 'yes' if disabled else False
        children.append({'born_before_2017': born_before_2017, 'disabled': disabled, 'high_rate': high_rate})

    lcw = input("Do you have limited capability for work (LCW)? (yes/no): ").strip().lower() == 'yes'
    lcwra = input("Do you have limited capability for work-related activity (LCWRA)? (yes/no): ").strip().lower() == 'yes'
    is_carer = input("Are you a carer? (yes/no): ").strip().lower() == 'yes'
    childcare_costs = float(input("Enter your childcare costs (if applicable, otherwise enter 0): "))
    capital = float(input("Enter your total capital (savings, investments, etc.): "))
    earnings = float(input("Enter your monthly earnings: "))
    receives_housing_support = input("Do you receive housing support? (yes/no): ").strip().lower() == 'yes'
    eligible_rent = float(input("Enter your eligible rent amount: "))
    non_dependants = int(input("Enter the number of non-dependants living with you: "))

    # Create claimant dictionary
    claimant = {
        'age': age,
        'is_single': is_single,
        'partner_age': partner_age,
        'children': children,
        'lcw': lcw,
        'lcwra': lcwra,
        'is_carer': is_carer,
        'childcare_costs': childcare_costs,
        'capital': capital,
        'earnings': earnings,
        'receives_housing_support': receives_housing_support,
        'eligible_rent': eligible_rent,
        'non_dependants': non_dependants
    }

    # Calculate final UC amount
    final_uc_amount = calculate_uc_eligibility(claimant)

    # Display the result
    print(f"Your estimated Universal Credit amount is: £{final_uc_amount:.2f}")
    print("Thank you for using the Universal Credit Calculator!")
    
# Run the interactive calculator if this script is executed directly
if __name__ == "__main__":
    uc_calculator()