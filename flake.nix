{
  description = "Python package for managing a network of notes.";

  inputs.nixpkgs.url = github:NixOS/nixpkgs/21.05;

  outputs = { self, nixpkgs, }:
    let
      supportedSystems = [ "x86_64-linux" "x86_64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs supportedSystems (system: f system);
    in
      {
        synapse = forAllSystems (system:
          with import nixpkgs { system = "${system}"; };

            python38Packages.buildPythonPackage {
              name = "synapse";
              src = ./.;
              propagatedBuildInputs = with python38Packages; [ 
                markdown
                networkx
                matplotlib
              ];
              nativeBuildInputs = with python38Packages; [ pytest mypy black sphinx sphinx_rtd_theme ];
              doCheck = false;
            }

          );

        defaultPackage = forAllSystems (system:
            self.synapse.${system}
          );
      };

}
