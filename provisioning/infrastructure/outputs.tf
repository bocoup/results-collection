output "master_public_ip" {
  value = "${aws_instance.build_master.public_ip}"
}

output "vpn_tunnel_address" {
  value = "${module.vpc.tunnel_address}"
}

output "vpn_tunnel_psk" {
  value = "${module.vpc.tunnel_psk}"
}
