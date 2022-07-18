{
  description = "Archival API with multi-provider and local freeze-dry support";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "nixpkgs/nixos-21.11";
  inputs.poetry2nix.url = "github:nix-community/poetry2nix";
  inputs.devshell.url = "github:numtide/devshell";

  outputs = { self, nixpkgs, flake-utils, poetry2nix, devshell }:
    let
      # Import the desired systems from flake-utils instead of strings, to avoid typos
      mySystems = with flake-utils.lib.system; [
        x86_64-linux
        x86_64-darwin
        aarch64-linux
      ];
    in
    {
      # Nixpkgs overlay providing the application
      overlay = nixpkgs.lib.composeManyExtensions [
        poetry2nix.overlay
        devshell.overlay
        (
          final: prev: {
            # The application
            arkive-api = prev.poetry2nix.mkPoetryApplication {
              projectDir = ./.;
            };

          }
        )
      ];
      # NOTE: the '//' operator below is used to merge the two sets.
      #       The overlay above is the same for all systems, but the rest of the
      #       attributes we must define for each desired system; so we iterate over
      #       them with 'eachSystem' below, then merge the results with the overlay.
    } // (
      # flake-utils.lib.eachDefaultSystem (
      flake-utils.lib.eachSystem mySystems (
        system:
        let
          pkgs = import nixpkgs {
            inherit system;
            overlays = [ self.overlay ];
          };

          inherit (pkgs) config lib;

          ## Docker image
          #    nix build '.#image'
          #    The resulting image can be loaded directly:
          #      docker load < result
          #    And executed:
          #      docker run -d --rm -p 3042:3042 arkive-api
          image = pkgs.dockerTools.buildLayeredImage {
            name = "arkive-api";
            tag = "latest";
            # The closure of config is automatically included in the closure of
            # the final image, so no need to explicitly set contents property.
            config = {
              Cmd = [
                "${pkgs.arkive-api}/bin/run"
              ];
              ExposedPorts = { "3042/tcp" = { }; };
            };
          };

        in
        rec
        {
          packages = {
            arkive-api-package = pkgs.arkive-api;
            # arkive-api-image = image;
            # arkive-api-tarball = tarball;
          };
          # 'nix build' to build default package
          defaultPackage = packages.arkive-api-package;

          # 'nix develop'
          devShell =
            let
              pyEnv = pkgs.poetry2nix.mkPoetryEnv {
                projectDir = ./.;
                editablePackageSources = {
                  arkive-api = ./arkive_api;
                };
              };
            in
            pkgs.devshell.mkShell {
              packages = with pkgs; [ pyEnv poetry ];

              commands = [
                { package = pkgs.poetry; }
                { package = pkgs.python3Packages.pytest; }
                { package = pkgs.nixpkgs-fmt; }
                { package = pkgs.black; }
              ];

            };

          # Use in your NixOS configuration:
          #   services.arkive-api.enable = true;
          #   services.arkive-api.db_path = /data/arkive.db
          #

          # nixosModule = import ./nixos;

          nixosModule = { config, lib, pkgs, ... }:
            let
              cfg = config.services.arkive-api;
            in
            {
              options = {
                services.arkive-api = {
                  enable = lib.mkEnableOption "enables arkive-api service";
                  # db_port = lib.mkOption {};
                  db_path = lib.mkOption {
                    type = lib.types.str;
                    example = "/data/arkive_db.sqlite";
                    description = "Path to sqlite database";
                  };
                  package = lib.mkOption {
                    type = lib.types.package;
                    default = self.defaultPackage.${system};
                  };
                };
              };

              config = lib.mkIf cfg.enable {
                # nixpkgs = { inherit (pkgs) overlays; };
                users.users.arkive = {
                  isSystemUser = true;
                  group = "arkive";
                  uid = 1024;
                };
                users.groups.arkive = { gid = 1024; };

                systemd.services.arkive-api = {
                  after = [ "network.target" ];
                  wantedBy = [ "multi-user.target" ];
                  environment = {
                    ARKIVE_DB_PATH = cfg.db_path;
                    # ARKIVE_DB_PORT = cfg.db_port;
                  };
                  serviceConfig = {
                    Type = "simple";
                    User = "arkive";
                    Group = "arkive";
                    ExecStart = "${cfg.package}/bin/run";
                  };
                };
              };

            };
        }
      )
    );
}
