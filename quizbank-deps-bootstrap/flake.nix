{
  description = "QuizBank dev shell with pinned system tools";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.python311
            pkgs.python311Packages.pip
            pkgs.uv
            pkgs.pre-commit
            pkgs.jq
            pkgs.yq
            pkgs.typst
            pkgs.pandoc
            pkgs.tectonic
            pkgs.graphviz
            pkgs.imagemagick
            pkgs.zip
            pkgs.unzip
          ];
          shellHook = ''
            export PIP_DISABLE_PIP_VERSION_CHECK=1
            echo "Dev shell ready. Run: uv sync"
          '';
        };
      });
}
