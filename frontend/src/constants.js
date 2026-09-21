export const STATUS_COLORS = {
  QUEUED: "default",
  IMPORTING: "blue",
  PROCESSING: "processing",
  COMPLETED: "success",
  FAILED: "error",
  CANCELLED: "warning",
  CANCELLING: "warning",
};

export const FILTER_TOGGLE_LABELS = [
  { key: "allowed_tld", label: "Allowed TLD" },
  { key: "invalid_email", label: "Invalid Email" },
  { key: "duplicate_email", label: "Duplicate Email" },
  { key: "duplicate_vs_master", label: "Duplicate vs Master" },
  { key: "personal_email", label: "Personal Email" },
  { key: "restricted_domain", label: "Restricted Domain" },
  { key: "restricted_keyword", label: "Restricted Keyword" },
  { key: "restricted_title", label: "Restricted Title" },
  { key: "restricted_industry", label: "Restricted Industry" },
  { key: "one_character_username", label: "One Character Username" },
  { key: "numeric_username", label: "Numeric Username" },
  { key: "username_equals_domain", label: "Username Equals Domain" },
  { key: "spam_domain", label: "Spam Domain" },
];

export const REASON_CODE_LABELS = {
  KEPT: "Final Kept",
  INVALID_EMAIL: "Invalid Email",
  OTHER_TLD: "Other TLD",
  DUPLICATE_EMAIL: "Duplicate Email",
  DUPLICATE_VS_MASTER: "Duplicate vs Master",
  PERSONAL_EMAIL: "Personal Email",
  RESTRICTED_DOMAIN: "Restricted Domain",
  RESTRICTED_KEYWORD: "Restricted Keyword",
  RESTRICTED_TITLE: "Restricted Title",
  RESTRICTED_INDUSTRY: "Restricted Industry",
  ONE_CHARACTER_USERNAME: "One Character Username",
  INVALID_NUMERIC_USERNAME: "Invalid Numeric Username",
  USERNAME_EQUALS_DOMAIN: "Username Equals Domain",
  SPAM_DOMAIN: "Spam Domain",
};
