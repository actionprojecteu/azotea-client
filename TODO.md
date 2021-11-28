
INMEDIATO
=========
* Modificaciones al modelo de datos:
  - añadir width and height a sky_brightness_v
  - CONSULTAR CON JAIME:
   - quitar columnas *dark* de sky_brightness_t
   - Documento de CSV de AZOTEA. Revisar y actualizar
   - Que me pase la base de datos y se la apaño

* azotuool image delete y azotool sky
- options [--all|--unpublished|--range|--latest-night|--latest-month] y --commit para borrar de verdad

* Herramienta de migracion (migration.py), dentro de azotool pero como un verdadero script aislado con sqlite a pelo

* enviar aggrement al server:
- URL subpath para el agreement
- UL subpath para las medidas

* A migrar:
- Izquierdo, Jaime                       Imagen de prueba [X]
- Zamorano, Jaime                        Imagen de prueba [X]
- Rodriguez, Diego                       Imagen de prueba [X]
- De Ferra, Enrique                      Imagen de prueba [X]
- De la Torre, Francisco Javier (Madrid) Imagen de prueba [X]
- García, Estebam (Motilla)              Imagen de prueba [X]
- Garrofé, Inma (Mollerussa)             Imagen de prueba [X]
- Hilera, Ignacio (Vitoria)              Imagen de prueba [X]
- Morales, Angel (Ribarroja)             Imagen de prueba [X]
- Navarro, Jose Luis (Hontecillas)       Imagen de prueba [X]
- Otero, Pablo (Madrid)                  Imagen de prueba [X]
- Jordán, Fernando (Requena)             Imagen de prueba [ ]
- García, Antonio                        Imagen de prueba [ ]

MEDIO PLAZO
===========


* ¿Validacion? _tkinter.TclError: expected floating-point number but got "39,6928888889"
* Probar la generacion del megaexport
* Falla el constraint check de borra imagenes/medidas.
* ¿ azotool sky publish ?
* Publicacionde medidas
  - Controlador (tanbto ewn GUI como en batch)
    - revisar codigo
    - hacerlo por páginas
    - enviar el consensitimeinto con su fecha
    - progress bar en relacion al numero de HTTP post a hacer
    - avisar de que va a tardar un rato (si hay que hacer > 2 peticiones HTTPS)

* Conectarse a un servidor web y publicar las medidas


* Bucle for roi in rois:
  procesar estadisticas (como soporte a tener uchas rois por imagen)


* ROI, definicion interactiva
  - cuadro de dialogo con canvas

* Boton de ver imagen al ver la ROI

* soporte para FITS
  - opciones de camara (bias, etc.)
  - proceso de registro

* backup y restore de la BD usando SQL

* Atajos de Teclado


* Multiidioma y  Localizacion en español

* TextWidget para ver los log
   - como se añaden observadores nuevos a twisted
   - como se inserta texto en el Text
   - Como se muestra/oculta esta cosa

* Tab "Miscelanea": poner posiblemente las reglas para los cuadros oscuros
  Cuadroroscuro:
  - o por cabecera
  - o por prefijo de fichero
  - o por sufijo de fichero


```python
RawPy
rgb_base_linear = raw_base.postprocess(output_color=rawpy.ColorSpace.raw, gamma=(1, 1),
                                       user_wb=[1.0, 1.0, 1.0, 1.0], no_auto_bright=True)
```

Interesnting links
==================

* [TKINTER reference](https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/index.html)

* [HOME variable in windows](https://superuser.com/questions/607105/is-the-home-environment-variable-normally-set-in-windows)

* [Link matplotlib backend to own canvas](https://pythonprogramming.net/how-to-embed-matplotlib-graph-tkinter-gui/)

* [gettext & .po HOWTO](https://phrase.com/blog/posts/translate-python-gnu-gettext/)

* [Using GetText](https://inventwithpython.com/blog/2014/12/20/translate-your-python-3-program-with-the-gettext-module/)

* [Dislay a numpy image](https://stackoverflow.com/questions/2659312/how-do-i-convert-a-numpy-array-to-and-display-an-image)

 beware of numy and PIL indexing 

* [Create and move a rectangle in a canvas](https://pythonprogramming.altervista.org/moving-a-rectangle-on-the-canvas-in-tkinter/?doing_wp_cron=1620111178.4584701061248779296875)

* [EXIF & Plate Scale](https://clarkvision.com/articles/platescale/)

* [Icons](https://commons.wikimedia.org/wiki/Tango_icons)

* [Jupyter and virtual envs](https://janakiev.com/blog/jupyter-virtual-envs/)

* [Tkinter & combobox](https://www.manejandodatos.es/2014/10/la-odisea-de-trabajar-con-combobox-en-tkinter/)

* https://towardsdatascience.com/raw-image-processing-in-python-238e5d582761

* https://docstore.mik.ua/orelly/perl3/tk/ch02_01.htm

* [EXIF standard tags](https://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif.html)


