docker pull stanfordaha/garnet:latest
# docker pull stanfordaha/garnet:onyx_tapeout

container_name=$1

docker run -it -d -v /cad:/cad -v /nobackup/owhsu:/aha/datasets/ --name ${container_name} stanfordaha/garnet:latest bash
# docker run -it -d -v /cad:/cad --name ${container_name} stanfordaha/garnet:onyx_tapeout bash

#docker cp ~/.ssh ${container_name}:/root/
#docker cp ~/.vimrc ${container_name}:/root/
docker exec -it -w /aha ${container_name} git config --global user.email "sgauthamr2001@gmail.com"
docker exec -it -w /aha ${container_name} apt update
docker exec -it -w /aha ${container_name} apt install vim -y
docker exec -it -w /aha ${container_name} apt install tmux -y
docker exec -it -w /aha ${container_name} tmux
