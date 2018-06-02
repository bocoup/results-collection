##
# This module manages a VPC for all of our infrastructure to exist in.
#
variable "name" { default = "vpc" }
variable "cidr" { }

output "id" { value = "${aws_vpc.main.id}" }
output "cidr" { value = "${aws_vpc.main.cidr_block}" }
output "vpn_gateway_id" { value = "${aws_vpn_gateway.main.id}" }

resource "aws_vpc" "main" {
  cidr_block = "${var.cidr}"
  enable_dns_hostnames = true
  enable_dns_support = true
  tags {
    Name = "${var.name}"
  }
}

# Consider relocating the following into a module

resource "aws_vpn_gateway" "main" {
  vpc_id = "${aws_vpc.main.id}"
  lifecycle {
    create_before_destroy = true
  }
  tags {
    Name = "${var.name}"
  }
}

resource "aws_customer_gateway" "customer_gateway" {
  bgp_asn    = 65000
  # The public IP address of the external machine
  ip_address = "135.84.57.36"
  type       = "ipsec.1"
  tags {
    Name = "${var.name}"
  }
}

resource "aws_vpn_connection" "main" {
  vpn_gateway_id      = "${aws_vpn_gateway.main.id}"
  customer_gateway_id = "${aws_customer_gateway.customer_gateway.id}"
  type                = "ipsec.1"
  static_routes_only  = true
}

output "tunnel_address" {
  value = "${aws_vpn_connection.main.tunnel1_address}"
}
output "tunnel_psk" {
  value = "${aws_vpn_connection.main.tunnel1_preshared_key}"
}
