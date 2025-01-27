import json


def lambda_handler(event, context):
    print(event)
    # Check if the event contains the required userAttributes
    user_attributes = event['request'].get('userAttributes', {})
    custom_role = user_attributes.get('custom:role', 'default_role')  # Default to 'default_role' if not found
    custom_org = user_attributes.get('custom:org', 'default_org')    # Default to 'default_org' if not found
    
    # Prepare the claims to be added or overridden
    claims_to_add = {
        'custom:role': custom_role,
        'custom:org': custom_org
    }

    # Add custom attributes to the claims in the response
    event['response']['claimsOverrideDetails'] = {
        'claimsToAddOrOverride': claims_to_add
    }

    # Log for debugging
    print("Claims to add:", claims_to_add)
    print(event)
    # Return the modified event
    return event
