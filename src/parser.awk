BEGIN{
y=1;
#print "anno;tipo;cod_comunidad;cod_provincia;cod_partido;siglas;votos;escannos" > "AUT_F1_T_R.ov"
FS=":";
CONVFMT = "%2.2f"
finish=0
}
{
	col = y % 4
	if(col == 1){
        	local=$2
        	if(local=="1")
                	exit "Ya no hay más apuestas"
	}
	if(col == 2){
                cuota_local=$2
        }
	if(col == 3){
                                visitante=$2
        }
	if(col == 0){
        	cuota_visitante=$2
                #print local " ("cuota_local") - "visitante " ("cuota_visitante")"
		#print "python3 app.py \"dota2\" \""local"\" \""visitante"\""
		system("python3 app.py \"dota2\" \""local"\" \""visitante"\" \""cuota_local"\" \""cuota_visitante"\"")
	}
	y++;

}
