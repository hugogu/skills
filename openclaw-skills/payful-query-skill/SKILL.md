---
name: payful-query
description: Query Payful account information including balance, transactions, and account details. Use when the user needs to check their Payful account status, view balance, or retrieve account information. Requires PAYFUL_TOKEN and PAYFUL_USER_ID environment variables to be set.
---

# Payful Query Skill

This skill queries Payful account information via the Payful API.

## Prerequisites

Set the following environment variables:
- `PAYFUL_TOKEN` - Authentication token (from BF-INTERNATIONAL-MEMBER-TOKEN cookie)
- `PAYFUL_USER_ID` - User ID (from AGL_USER_ID cookie)

## Usage

### Query Account Balance

```python
python scripts/query_balance.py
```

### Query with Custom API URL

If using a different Payful environment:

```python
python scripts/query_balance.py --api-url https://other.payful.com
```

## API Reference

The skill uses the following Payful API endpoints:

### Get Account Balance
- **URL**: `https://global.payful.com/api/user/account/queryUserAccBalByHomePage`
- **Method**: GET
- **Headers**:
  - `Accept: application/json, text/plain, */*`
  - `Accept-Language: zh-CN`
  - `request-system-name: member-exchange-client`
  - `Cookie`: Contains authentication tokens

## Response Format

```json
{
  "code": "0000",
  "data": {
    "totalBalance": "1234.56",
    "currency": "USD",
    "availableBalance": "1200.00",
    "frozenBalance": "34.56"
  },
  "message": "success"
}
```
