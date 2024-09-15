#Setup
sudo apt-get install wget git chromium-browser
pip install fastapi uvicorn
pip install youtube-dl
pip install archivebox
pip install python-multipart

snap install chromium
archivebox init

or
sudo add-apt-repository ppa:saiarcot895/chromium-beta
sudo apt update
sudo apt install chromium-browser

sudo apt update
sudo apt install nodejs npm

//npm install -g single-file
npm install -g "single-file-cli"

##Probably I should put all of this in a comfortable ready to use docker

#Run
uvicorn main:app --reload
