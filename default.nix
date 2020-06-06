{
  pkgs ? import <nixpkgs> {},
  pythonPackages ? pkgs.python37Packages,
  forTest ? true
}:
{
  cpytraceaflRegexEnv = pkgs.stdenv.mkDerivation {
    name = "cpytraceafl-regex-env";
    buildInputs = [
      (pythonPackages.buildPythonPackage rec {
        pname = "cpytraceafl";
        version = "0.7.0";

        src = pkgs.fetchFromGitHub {
          owner = "risicle";
          repo = pname;
          rev = "v${version}";
          sha256 = "1s5633wj1nlzvwn6qva29ajbdmra728x1b5i1ml6asj5b85sam55";
        };

        buildInputs = [ pythonPackages.pytestrunner ];
        propagatedBuildInputs = [ pythonPackages.sysv_ipc ];

        checkInputs = [ pythonPackages.pytest ];
        dontStrip = true;
      })
      pythonPackages.setuptools
    ] ++ pkgs.stdenv.lib.optionals forTest [
      pythonPackages.pytest
      pythonPackages.pytestrunner
    ];
  };
}
