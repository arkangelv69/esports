BEGIN{
y=1;
FS=":";
CONVFMT = "%2.2f"
finish=0
}
{
    #print $2
	col = y % 5
	if(col == 1){
        name_serie=$2
	}
	if(col == 2){
	    local=$2
        if(local=="1")
            exit "Ya no hay más apuestas"

    }
	if(col == 3){
	    cuota_local=$2

    }
    if(col == 4){
        visitante=$2
    }
	if(col == 0){
	    cuota_visitante=$2
        print local " ("cuota_local") - "visitante " ("cuota_visitante") -- " name_serie
		#print "python3 app.py \"dota2\" \""local"\" \""visitante"\""
	    system("python3 app.py \""name_serie"\" \""local"\" \""cuota_local"\" \""visitante"\" \""cuota_visitante"\"")
	}
	y++;

}
