{ config, lib, pkgs, ... }: let
  cfg = config.services.arkive-api;
in
{
  options = {
    services.arkive-api = {
      enable = lib.mkEnableOption "enables arkive-api service";
      db_path = lib.mkOption {
        type = lib.types.path;
        example = /home/user/arkive_db.sqlite;
        description = "Path to sqlite database";
      };
      package = lib.mkOption {
        type = lib.types.package;
        default = self.defaultPackage;
      };
    };
  };

  config = lib.mkIf cfg.enable {
    nixpkgs.overlays = [ self.overlay ];
    users.users.arkive.isSystemUser = true;

    systemd.services.arkive-api = {
      after = [ "network.target" ];
      serviceConfig = {
        Type = "simple";
        User = "arkive";
        Group = "arkive";
        ExecStart = "${cfg.package}/bin/prod";
      };
    };
  };
}
