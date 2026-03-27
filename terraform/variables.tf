variable "credentials" {
  description = "My Credentials"
  default     = "../99_secrets/svc_terra.json"
}


variable "project" {
  description = "Project"
  default     = "real-crypto-hc"
}

variable "region" {
  description = "Region"
  default     = "europe-west2"
}

variable "location" {
  description = "Project Location"
  default     = "EU"
}

variable "bq_dataset_name" {
  description = "My BigQuery Dataset Name"
  #Update the below to what you want your dataset to be called
  default     = "crypto"
}

variable "gcs_bucket_name" {
  description = "My Storage Bucket Name"
  #Update the below to a unique bucket name
  default     = "real-crypto-bucket"
}

variable "gcs_storage_class" {
  description = "Bucket Storage Class"
  default     = "STANDARD"
}