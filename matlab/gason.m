function out = gason(in)
%GASON Octave-compatible JSON wrapper that shadows the vendored COCO copy.

if ischar(in)
  out = jsondecode(in) ;
else
  out = jsonencode(in) ;
end
