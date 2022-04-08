#!/bin/bash
directory=${1:-origin}                                                         
sizelimit=${2:-20}                                                  
sizesofar=0                                                                     
dircount=1
du -s -k "$directory"/* | while read -r size file                  
do
  echo "size:$size , file:$file"                                   
  if ((sizesofar + size > sizelimit))                                           
  then                                                                          
    (( dircount++ ))                                                            
    sizesofar=0
  fi                                                                            
  (( sizesofar += size ))                                                       
  echo "dircount: $dircount ; sizesofar: $sizesofar"                                                              

  # create the plan instead of copying?

  #mkdir -p -- "$directory/sub_$dircount"                                           
  #cp -- "$file" "$directory/sub_$dircount"                                           
done 
