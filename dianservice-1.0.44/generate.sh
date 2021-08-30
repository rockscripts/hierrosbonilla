#sudo rm -r /odoo_peru/custom/addons_demo/sunat_fact/service/sunatservice/sunatservice.egg-info
#sudo rm -r /odoo_peru/custom/addons_demo/sunat_fact/service/sunatservice/dist
#sudo rm -r /odoo_peru/custom/addons_demo/sunat_fact/service/sunatservice/build

python3 setup.py bdist_egg
#sudo python3 setup.py bdist
python3 setup.py bdist_rpm
python3 setup.py install
#sudo python setup.py bdist_egg
#sudo python setup.py bdist
#sudo python setup.py bdist_rpm
#sudo python setup.py install

#twine upload --repository-url https://upload.pypi.org/legacy/  dist/*

#pip3 install -U sunatservice

#sudo pip uninstall sunatservice
#sudo pip3 uninstall sunatservice -y


#Consulta RUC
#sudo apt-get install tesseract-ocr tesseract-ocr-eng phantomjs
#pip install -r pip-requirements.txt
#pip install vatnumber

#sudo mv /home/USUARIO/.local/lib/python3.6/site-packages/xmlsec* /usr/local/lib/python3.6/dist-packages
#sudo mv /home/USUARIO/.local/lib/python3.6/site-packages/bs4* /usr/local/lib/python3.6/dist-packages
#sudo mv /home/USUARIO/.local/lib/python3.6/site-packages/pytesseract* /usr/local/lib/python3.6/dist-packages