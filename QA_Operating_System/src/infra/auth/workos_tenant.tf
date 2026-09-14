# HUMAN-OWNED: WorkOS tenant configuration
# Staged: Live SSO/SCIM configured at first design-partner onboarding
terraform {
  required_providers {
    workos = { source = "workos/workos", version = "~> 0.1" }
  }
}
