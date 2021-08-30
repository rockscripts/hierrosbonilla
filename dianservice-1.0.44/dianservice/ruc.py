import requests
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
import os, re, json, sys


class Ruc:
   endPoint = 'http://versionanterior.rues.org.co/RUES_Web/Consultas/ConsultaNIT_json'
   maxTries = 2
   maxTried = 1
   xmlPath = ''

   def consultNIT(self,nit):
      raiz = self.endPoint
      
      sesion = requests.session()
      response = {}
      
      try:
         formdata =  {
                        'strNIT': str(nit)
                     }
         # with open('/home/rockscripts/Documents/data.json', 'w') as outfile:
         #    json.dump(resultado.content.decode('utf-8'), outfile)
         resultado = sesion.post(raiz, data=formdata, verify=False)         
         
         if( not hasattr(resultado, 'status_code')!=200 ):
            response["error"] = "Servicio no disponible temporalmente."
            return response

         profile = {}
         profile = json.loads(resultado.content.decode('utf-8'), encoding='utf-8')

         

         if('codigo_error' in profile):
            if(profile['codigo_error']=="0000"):
               response['tipo_identificacion']  = profile['rows'][0]["tipoID"]
               response['denominacion']  = profile['rows'][0]["razSol"]
               response['camara_comercio']  = profile['rows'][0]["desc_camara"]
               response['regimen']  = profile['rows'][0]["desc_categoria_matricula"]
               mas_detalles = profile['rows'][0]["detalleRM"]
               index = str(mas_detalles).index("matricula=")
               matricula = mas_detalles[index+10:-7]
               response['matricula']  = matricula
            else:
               response["error"] = "No hay resultados en la DIAN, vuelve a intentar."
               response["profile"] = profile
               return response
         else:
            response["error"] = "Servicio no disponible temporalmente."
            return response

         

      except Exception as e:
            exc_traceback = sys.exc_info()
            #with open('/home/rockscripts/Documents/data.json', 'w') as outfile:
            #   json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
            response = "Servicio no disponible temporalmente."+"\n\n"+ getattr(e, 'message', repr(e))+str(repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno)                        
            return response

      return response
   
   def setXMLPath(self, xmlPath):
      self.xmlPath = xmlPath
               