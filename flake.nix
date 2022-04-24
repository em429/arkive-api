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
          arkive-py = prev.poetry2nix.mkPoetryApplication {
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
          package = pkgs.arkive-py;
          # image = pkgs.arkive-py.image;
          # tarball = pkgs.arkive-py.tarball;
        };
        # 'nix build' to build default package
        defaultPackage = packages.package;

        apps = {
          arkive-py = pkgs.arkive-py;
        };
        defaultApp = pkgs.arkive-py;
      }));
}
