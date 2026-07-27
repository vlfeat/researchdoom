# Run the full CocoDoom extraction process using the legacy code
# Paths are hardcoded to /tmp/cocodoom-legacy-raw, /tmp/cocodoom-legacy-tmp, /tmp/cocodoom-legacy
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "cocodoom-record.sh"
"$SCRIPT_DIR/cocodoom-record.sh"

echo "cocodoomGen"
octave --quiet --eval "pkg load image datatypes; addpath(fullfile('$ROOT_DIR', 'matlab')); cocodoomGen"

echo "cocodoomSplit"
octave --quiet --eval "pkg load image datatypes; addpath(fullfile('$ROOT_DIR', 'matlab')); cocodoomSplit"

echo "cocodoomTest"
octave --quiet --eval "pkg load image datatypes; addpath(fullfile('$ROOT_DIR', 'matlab')); cocodoomTest"

echo "cocodoomGallery"
octave --quiet --eval "pkg load image datatypes; addpath(fullfile('$ROOT_DIR', 'matlab')); cocodoomGallery"

echo "cocodoom-pack.sh"
"$SCRIPT_DIR/cocodoom-pack.sh"