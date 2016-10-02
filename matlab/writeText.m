function writeText(fileName, txt)
f = fopen(fileName,'w') ;
fwrite(f,txt) ;
fclose(f) ;
