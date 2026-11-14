window.TL = {
 "fps": 30,
 "total": 118.452,
 "scenes": [
  {
   "id": "01",
   "start": 0.0,
   "end": 10.426,
   "voice": "ElevenLabs, voz Camila ES, modelo eleven_v4",
   "s": [
    {
     "start": 0.35,
     "end": 10.102,
     "text": "Quórum es una compuerta determinista: impide que un dato sellado salga publicado, aunque el ataque se reparta entre varios agentes de inteligencia artificial."
    }
   ]
  },
  {
   "id": "02",
   "start": 10.426,
   "end": 23.319,
   "voice": "ElevenLabs, voz Camila ES, modelo eleven_v4",
   "s": [
    {
     "start": 10.426,
     "end": 16.064,
     "text": "El caso: tres agentes tramitan una licitación pública con ofertas selladas."
    },
    {
     "start": 16.179,
     "end": 19.569,
     "text": "Uno radica, otro evalúa y otro publica."
    },
    {
     "start": 19.607,
     "end": 22.998,
     "text": "Si el ataque se reparte, ningún paso se ve raro."
    }
   ]
  },
  {
   "id": "03",
   "start": 23.319,
   "end": 35.526,
   "voice": "ElevenLabs, voz Camila ES, modelo eleven_v4",
   "s": [
    {
     "start": 23.319,
     "end": 28.652,
     "text": "Cada dato lleva la etiqueta de sus fuentes, y lo que un agente escribe la hereda."
    },
    {
     "start": 28.728,
     "end": 35.204,
     "text": "En cada salida, la compuerta compara etiquetas: no lee texto ni llama a ningún modelo."
    }
   ]
  },
  {
   "id": "04",
   "start": 35.526,
   "end": 43.13,
   "voice": "ElevenLabs, voz Camila ES, modelo eleven_v4",
   "s": [
    {
     "start": 35.526,
     "end": 39.031,
     "text": "Así se ve funcionando, con datos sintéticos."
    },
    {
     "start": 39.107,
     "end": 42.307,
     "text": "En un trámite honesto, la adjudicación se publica."
    }
   ]
  },
  {
   "id": "05",
   "start": 43.13,
   "end": 53.354,
   "voice": "ElevenLabs, voz Camila ES, modelo eleven_v4",
   "s": [
    {
     "start": 43.13,
     "end": 48.311,
     "text": "Con los tres agentes desviados, el valor sellado pasa de uno a otro."
    },
    {
     "start": 48.349,
     "end": 52.502,
     "text": "La compuerta bloquea la salida: no se publica nada."
    }
   ]
  },
  {
   "id": "06",
   "start": 53.354,
   "end": 69.452,
   "voice": "ElevenLabs, voz Camila ES, modelo eleven_v4",
   "s": [
    {
     "start": 53.354,
     "end": 57.125,
     "text": "Lo medimos en noventa trámites con agentes de modelo."
    },
    {
     "start": 57.163,
     "end": 61.925,
     "text": "Sin defensa, el valor se fugó en dieciséis de treinta ataques."
    },
    {
     "start": 61.963,
     "end": 69.201,
     "text": "La compuerta bloqueó las dieciséis fugas y dejó pasar los sesenta trámites honestos, sin llamar a un modelo."
    }
   ]
  },
  {
   "id": "07",
   "start": 69.452,
   "end": 81.434,
   "voice": "ElevenLabs, voz Camila ES, modelo eleven_v4",
   "s": [
    {
     "start": 69.452,
     "end": 74.278,
     "text": "Un monitor por agente también las detecta, sin falsos positivos."
    },
    {
     "start": 74.302,
     "end": 81.185,
     "text": "Pero gasta tres llamadas a un modelo por trámite y califica al final: detecta, no detiene."
    }
   ]
  },
  {
   "id": "08",
   "start": 81.434,
   "end": 96.243,
   "voice": "ElevenLabs, voz Camila ES, modelo eleven_v4",
   "s": [
    {
     "start": 81.434,
     "end": 89.358,
     "text": "En cinco dominios, con agentes que siguen un guion, dejó en cero el daño en siete mil seiscientos episodios adversos."
    },
    {
     "start": 89.587,
     "end": 95.911,
     "text": "Y en trazas públicas de AgentDojo frenó mil quinientos seis de mil quinientos veintiún secuestros."
    }
   ]
  },
  {
   "id": "09",
   "start": 96.243,
   "end": 111.806,
   "voice": "ElevenLabs, voz Camila ES, modelo eleven_v4",
   "s": [
    {
     "start": 96.243,
     "end": 97.615,
     "text": "Tiene costos."
    },
    {
     "start": 97.729,
     "end": 102.148,
     "text": "Bloquea siempre al agente honesto que abre un sobre que no necesitaba."
    },
    {
     "start": 102.186,
     "end": 106.034,
     "text": "En AgentDojo detiene parte de las tareas legítimas."
    },
    {
     "start": 106.072,
     "end": 111.557,
     "text": "Y un rival externo puede recuperar el monto con los puntajes que la licitación publica."
    }
   ]
  },
  {
   "id": "10",
   "start": 111.806,
   "end": 118.452,
   "voice": "ElevenLabs, voz Camila ES, modelo eleven_v4",
   "s": [
    {
     "start": 111.806,
     "end": 116.225,
     "text": "El código, los datos y los límites están en el repositorio."
    }
   ]
  }
 ]
};
