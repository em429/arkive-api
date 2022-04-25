{
  description = "Archival API with multi-provider and local freeze-dry support";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "nixpkgs/nixos-21.11";
  inputs.poetry2nix.url = "github:nix-community/poetry2nix";

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    {
      # Nixpkgs overlay providing the application
      overlay = nixpkgs.lib.composeManyExtensions [
        poetry2nix.overlay
        (final: prev: {
          # The application
          arkive-api = prev.poetry2nix.mkPoetryApplication {
            projectDir = ./.;
          };
        })
      ];

    } // (flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ self.overlay ];
        };
      in rec
      {
        packages = {
          package = pkgs.arkive-api;
          # image = pkgs.arkive-api.image;
          # tarball = pkgs.arkive-api.tarball;
        };

        # 'nix build' to build default package
        defaultPackage = packages.package;

        apps = {
          arkive-api = pkgs.arkive-api;
        };
        defaultApp = pkgs.arkive-api;

        nixosModules.arkive-api = { pkgs, ...}: {
            options = {
                services.arkive-api = {
                    enable = lib.mkEnableOption "enables arkive-api service";
                    db_path = lib.mkOption {
                        type = lib.types.path;
                        example = /home/user/arkive_db.sqlite;
                        description = "Path to sqlite database";
                    };
                    package = mkOption {
                        type = lib.types.package;
                        default = self.defaultPackage;
                    };
                };
            };

            config = lib.mkIf config.services.arkive-api.enable {
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
        };

      }));
}
