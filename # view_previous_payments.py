# view_previous_payments.py
# This script is designed to display a user's previous Universal Credit payments.
# It is part of a larger system that helps users manage their Universal Credit claims.
# The script is written in Python 3 and uses standard libraries to handle data formatting and output.

# It takes a list of payment history and prints out the details in a formatted manner.


NO_PAYMENTS_MESSAGE = "No previous payments found."

def payments(payment_history):
    """
    Displays a user's previous Universal Credit payments.

    Args:
        payment_history (list of dict): A list of dictionaries where each dictionary contains
                                        details of a payment (e.g., date, amount).

    Notes:
        - If `payment_history` is empty, a message ("No previous payments found.") is printed,
          and the function returns early.
        - If a payment dictionary is missing required keys ('date' and/or 'amount'), an error
          message is printed for that entry.
        - The amount is formatted to two decimal places and prefixed with the pound symbol (£)
          for proper currency representation.

    Example:
        payment_history = [
            {"date": "2023-01-15", "amount": 250.00},
            {"date": "2023-02-15", "amount": 250.00},
        ]
    """
    if not payment_history:
        print(NO_PAYMENTS_MESSAGE)
        return

    print("Previous Universal Credit Payments:")
    print("-" * 40)
    # Format the amount to two decimal places and prefix it with the pound symbol (£)
    for payment in payment_history:
        if 'date' in payment and 'amount' in payment:
            print(f"Date: {payment['date']}, Amount: £{payment['amount']:.2f}")
        else:
            print("Error: Payment entry is missing required keys ('date' and/or 'amount').")
    print("-" * 40)
    print("-" * 40)

# Example usage
if __name__ == "__main__":
    # Example payment history
    payments = [
        {"date": "2023-01-15", "amount": 250.00},
        {"date": "2023-02-15", "amount": 250.00},
    ]
    payments(payments)