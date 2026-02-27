variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "project_name" {
  description = "Project name used as prefix for all resources"
  type        = string
  default     = "hackathon"
}

variable "region" {
  description = "Azure region for all resources"
  type        = string
  default     = "westeurope"
}

variable "node_vm_size" {
  description = "VM size for the AKS node pool"
  type        = string
  default     = "Standard_B2ms"
}

variable "node_count" {
  description = "Number of nodes in the AKS default pool"
  type        = number
  default     = 1
}
