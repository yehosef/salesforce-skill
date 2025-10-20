# Salesforce Metadata Types Reference

Common metadata types for deployment and retrieval using the sf CLI.

## Code Components

### ApexClass
Apex classes (business logic, controllers, utilities)

**Retrieve:**
```bash
# All Apex classes
sf project retrieve start -m "ApexClass" -o <alias>

# Specific class
sf project retrieve start -m "ApexClass:PaymentsBL" -o <alias>
```

**Deploy:**
```bash
sf project deploy start -m "ApexClass:MyClass" -o <alias>
```

---

### ApexTrigger
Apex triggers (automation on DML operations)

```bash
sf project retrieve start -m "ApexTrigger" -o <alias>
sf project retrieve start -m "ApexTrigger:AccountTrigger" -o <alias>
```

---

### ApexPage
Visualforce pages

```bash
sf project retrieve start -m "ApexPage" -o <alias>
sf project retrieve start -m "ApexPage:MyVFPage" -o <alias>
```

---

### ApexComponent
Visualforce components

```bash
sf project retrieve start -m "ApexComponent" -o <alias>
```

---

### AuraDefinitionBundle
Aura Lightning components (older Lightning framework)

```bash
sf project retrieve start -m "AuraDefinitionBundle" -o <alias>
sf project retrieve start -m "AuraDefinitionBundle:CreatePayments" -o <alias>
```

---

### LightningComponentBundle
Lightning Web Components (modern Lightning framework)

```bash
sf project retrieve start -m "LightningComponentBundle" -o <alias>
sf project retrieve start -m "LightningComponentBundle:myComponent" -o <alias>
```

---

## Objects & Fields

### CustomObject
Custom objects and standard objects with customizations

```bash
# All custom objects
sf project retrieve start -m "CustomObject" -o <alias>

# Specific custom object
sf project retrieve start -m "CustomObject:Standing_Order_Info__c" -o <alias>

# Standard object with customizations
sf project retrieve start -m "CustomObject:Account" -o <alias>
```

---

### CustomField
Custom fields (usually retrieved with CustomObject)

```bash
# Specific field
sf project retrieve start -m "CustomField:Account.Custom_Field__c" -o <alias>
```

---

### RecordType
Record types for objects

```bash
sf project retrieve start -m "RecordType" -o <alias>
sf project retrieve start -m "RecordType:Account.Business_Account" -o <alias>
```

---

### FieldSet
Field sets for dynamic layouts

```bash
sf project retrieve start -m "FieldSet" -o <alias>
```

---

### ValidationRule
Validation rules for objects

```bash
sf project retrieve start -m "ValidationRule" -o <alias>
```

---

### CompactLayout
Compact layouts for objects

```bash
sf project retrieve start -m "CompactLayout" -o <alias>
```

---

## Automation

### Flow
Flows (Screen Flows, Auto-launched Flows, Record-Triggered Flows)

```bash
sf project retrieve start -m "Flow" -o <alias>
sf project retrieve start -m "Flow:My_Flow" -o <alias>
```

---

### WorkflowRule
Workflow rules (legacy automation)

```bash
sf project retrieve start -m "WorkflowRule" -o <alias>
```

---

### ApprovalProcess
Approval processes

```bash
sf project retrieve start -m "ApprovalProcess" -o <alias>
```

---

### AssignmentRule
Assignment rules (Lead, Case)

```bash
sf project retrieve start -m "AssignmentRules" -o <alias>
```

---

### AutoResponseRule
Auto-response rules (Case, Lead)

```bash
sf project retrieve start -m "AutoResponseRules" -o <alias>
```

---

## User Interface

### Layout
Page layouts

```bash
sf project retrieve start -m "Layout" -o <alias>
sf project retrieve start -m "Layout:Account-Account Layout" -o <alias>
```

---

### CustomTab
Custom tabs

```bash
sf project retrieve start -m "CustomTab" -o <alias>
```

---

### CustomApplication
Custom apps

```bash
sf project retrieve start -m "CustomApplication" -o <alias>
```

---

### ListView
List views

```bash
sf project retrieve start -m "ListView" -o <alias>
```

---

### FlexiPage
Lightning pages (App, Home, Record pages)

```bash
sf project retrieve start -m "FlexiPage" -o <alias>
sf project retrieve start -m "FlexiPage:Account_Record_Page" -o <alias>
```

---

### CustomMetadata
Custom Metadata Types

```bash
sf project retrieve start -m "CustomMetadata" -o <alias>
```

---

## Security

### Profile
User profiles

```bash
sf project retrieve start -m "Profile" -o <alias>
sf project retrieve start -m "Profile:Admin" -o <alias>
```

---

### PermissionSet
Permission sets

```bash
sf project retrieve start -m "PermissionSet" -o <alias>
sf project retrieve start -m "PermissionSet:Sales_User" -o <alias>
```

---

### SharingRules
Sharing rules (ownership-based, criteria-based)

```bash
sf project retrieve start -m "SharingRules" -o <alias>
```

---

### Role
Roles and role hierarchy

```bash
sf project retrieve start -m "Role" -o <alias>
```

---

### Group
Public groups and queues

```bash
sf project retrieve start -m "Group" -o <alias>
```

---

## Configuration

### CustomSettings
Custom settings (hierarchy, list)

```bash
sf project retrieve start -m "CustomSettings" -o <alias>
```

---

### RemoteSiteSetting
Remote site settings for callouts

```bash
sf project retrieve start -m "RemoteSiteSetting" -o <alias>
```

---

### NamedCredential
Named credentials for authentication

```bash
sf project retrieve start -m "NamedCredential" -o <alias>
```

---

### CustomLabel
Custom labels for translations

```bash
sf project retrieve start -m "CustomLabels" -o <alias>
```

---

### StaticResource
Static resources (JS, CSS, images)

```bash
sf project retrieve start -m "StaticResource" -o <alias>
sf project retrieve start -m "StaticResource:MyJavaScript" -o <alias>
```

---

### EmailTemplate
Email templates

```bash
sf project retrieve start -m "EmailTemplate" -o <alias>
```

---

### GlobalValueSet
Global picklist value sets

```bash
sf project retrieve start -m "GlobalValueSet" -o <alias>
```

---

### StandardValueSet
Standard picklist value sets

```bash
sf project retrieve start -m "StandardValueSet" -o <alias>
```

---

## Reports & Dashboards

### Report
Reports

```bash
sf project retrieve start -m "Report" -o <alias>
```

---

### Dashboard
Dashboards

```bash
sf project retrieve start -m "Dashboard" -o <alias>
```

---

### ReportType
Custom report types

```bash
sf project retrieve start -m "ReportType" -o <alias>
```

---

## Common Retrieval Patterns

### Retrieve All Code
```bash
sf project retrieve start -m "ApexClass, ApexTrigger, ApexPage, ApexComponent, AuraDefinitionBundle, LightningComponentBundle" -o <alias>
```

### Retrieve All Custom Objects
```bash
sf project retrieve start -m "CustomObject" -o <alias>
```

### Retrieve All Automation
```bash
sf project retrieve start -m "Flow, WorkflowRule, ApprovalProcess" -o <alias>
```

### Retrieve All Security
```bash
sf project retrieve start -m "Profile, PermissionSet, SharingRules" -o <alias>
```

### Retrieve Everything (package.xml)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>*</members>
        <name>ApexTrigger</name>
    </types>
    <types>
        <members>*</members>
        <name>AuraDefinitionBundle</name>
    </types>
    <types>
        <members>*</members>
        <name>LightningComponentBundle</name>
    </types>
    <types>
        <members>*</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>*</members>
        <name>Flow</name>
    </types>
    <types>
        <members>*</members>
        <name>Layout</name>
    </types>
    <types>
        <members>*</members>
        <name>Profile</name>
    </types>
    <types>
        <members>*</members>
        <name>PermissionSet</name>
    </types>
    <version>60.0</version>
</Package>
```

Then:
```bash
sf project retrieve start -x manifest/package.xml -o <alias>
```

---

## Metadata API Version

Always specify the API version in package.xml:

```xml
<version>60.0</version>  <!-- Winter '24 -->
<version>61.0</version>  <!-- Spring '24 -->
<version>62.0</version>  <!-- Summer '24 -->
<version>63.0</version>  <!-- Winter '25 -->
```

Check current API version:
```bash
sf org display -o <alias>
```

---

## Tips

1. **Use wildcards carefully** - `*` retrieves ALL instances of a type
2. **Check dependencies** - Some metadata depends on others (deploy order matters)
3. **Standard objects** - Only retrieve if they have customizations
4. **Managed packages** - Cannot retrieve managed components
5. **Full names** - Use exact API names (case-sensitive)

---

## Common Deployment Order

To avoid dependency errors, deploy in this order:

1. Custom Objects
2. Custom Fields
3. Record Types
4. Page Layouts
5. Validation Rules
6. Workflows
7. Apex Classes (without triggers)
8. Triggers
9. Flows
10. Permission Sets / Profiles
11. UI Components (Aura/LWC)

---

## Resources

- **Metadata API Developer Guide**: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/
- **Metadata Coverage Report**: https://mdcoverage.secure.force.com/
