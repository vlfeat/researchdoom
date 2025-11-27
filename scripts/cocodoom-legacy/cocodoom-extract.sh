# Run the full CocoDoom extraction process using the legacy code
# Paths are hardcoded to /tmp/cocodoom-legacy-raw, /tmp/cocodoom-legacy-tmp, /tmp/cocodoom-legacy
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

"$SCRIPT_DIR/cocodoom-record.sh"
octave --quiet --eval "pkg load image datatypes; addpath(fullfile('$ROOT_DIR', 'matlab')); cocodoomGen"
octave --quiet --eval "pkg load image datatypes; addpath(fullfile('$ROOT_DIR', 'matlab')); cocodoomSplit"
octave --quiet --eval "pkg load image datatypes; addpath(fullfile('$ROOT_DIR', 'matlab')); cocodoomTest"
octave --quiet --eval "pkg load image datatypes; addpath(fullfile('$ROOT_DIR', 'matlab')); cocodoomGallery"
"$SCRIPT_DIR/cocodoom-pack.sh"