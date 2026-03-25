terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.6.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials)
  project     = var.project
  region      = var.region
}


resource "google_storage_bucket" "demo-bucket" {
  name          = var.gcs_bucket_name
  location      = var.location
  force_destroy = true
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
    
  }
}



resource "google_bigquery_dataset" "demo_dataset" {
  dataset_id = var.bq_dataset_name
  location   = var.location
}

resource "google_bigquery_table" "default" {
  dataset_id          = var.bq_dataset_name
  table_id            = "ticker"
  deletion_protection = false

  time_partitioning {
    type  = "HOUR"
    field = "window_start"
  }

  clustering = ["product_id"]

  schema = jsonencode([
    { name = "product_id",       type = "STRING",    mode = "REQUIRED" },
    { name = "window_start",     type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "window_end",       type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "price",            type = "FLOAT64",   mode = "REQUIRED" },
    { name = "low_24h",          type = "FLOAT64",   mode = "REQUIRED" },
    { name = "high_24h",         type = "FLOAT64",   mode = "REQUIRED" },
    { name = "price_per_chg_24h",type = "FLOAT64",   mode = "NULLABLE" },
    { name = "volume",           type = "FLOAT64",   mode = "REQUIRED" },
    { name = "best_ask",         type = "FLOAT64",   mode = "REQUIRED" },
    { name = "best_bid",         type = "FLOAT64",   mode = "REQUIRED" },
    { name = "spread",         type = "FLOAT64",   mode = "REQUIRED" },
    { name = "day_vlty",         type = "FLOAT64",   mode = "REQUIRED" },
    { name = "ind_vlty",         type = "FLOAT64",   mode = "REQUIRED" },

  ])
}