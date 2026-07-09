import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Cliente de Groq
cliente = Groq(api_key=os.getenv("GROQ_API_KEY"))

def resumir_solicitud_para_jefe(nombre_empleado: str, dias_solicitados: int, 
                                 fecha_inicio: str, fecha_fin: str, 
                                 motivo: str, dias_disponibles: int,
                                 total_solicitudes: int):
    """Genera un resumen de la solicitud para ayudar al jefe a decidir"""
    
    prompt = f"""Eres un asistente de RRHH. Resume en 2-3 oraciones cortas y directas esta solicitud de vacaciones para que el jefe pueda decidir rápido. 
    
Datos:
- Empleado: {nombre_empleado}
- Solicita: {dias_solicitados} días ({fecha_inicio} al {fecha_fin})
- Motivo: {motivo}
- Días disponibles en su saldo: {dias_disponibles}
- Solicitudes anteriores este año: {total_solicitudes}

Sé directo y menciona si el saldo alcanza o no. No uses listas, solo texto corrido."""

    respuesta = cliente.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )
    
    return respuesta.choices[0].message.content

def sugerir_comentario_rrhh(nombre_empleado: str, dias_solicitados: int,
                             fecha_inicio: str, fecha_fin: str,
                             dias_disponibles: int, decision: str):
    """Sugiere un comentario profesional para RRHH al confirmar o rechazar"""
    
    prompt = f"""Eres un asistente de RRHH. Redacta un comentario corto y profesional (máximo 2 oraciones) para {decision} esta solicitud de vacaciones.

Datos:
- Empleado: {nombre_empleado}
- Días solicitados: {dias_solicitados} ({fecha_inicio} al {fecha_fin})
- Días disponibles: {dias_disponibles}
- Decisión: {decision}

Solo escribe el comentario, sin explicaciones adicionales."""

    respuesta = cliente.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    )
    
    return respuesta.choices[0].message.content