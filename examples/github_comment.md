## 🛡️ Underwrite: Governance Review Failed

**Merge Blocked:** This PR introduces changes that violate deterministic governance policies.

### Violation Summary
- **Policy:** Target Leakage Prevention Policy
- **Evidence:** Column dropped: `customer_status`
- **Affected assets:** 11 dashboards, 2 ML models
- **Decision:** Block merge
- **Risk Score:** 94

### Visual Explanation
❌ **Required Column Removed**

`customer_status`
↓
11 dashboards, 2 ML models
↓
**Risk Score 94**

---
*This decision was driven by the DataHub metadata graph. An incident has been opened automatically.*
