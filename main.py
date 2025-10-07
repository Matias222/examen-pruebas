from fastapi import FastAPI
from app.routers import autores, libros, copias, lectores, prestamos, bioalert

app = FastAPI(
    title="Sistema de Biblioteca",
    description="API REST para gestión de biblioteca con sistema BioAlert",
    version="1.0.0"
)

# Incluir routers
app.include_router(autores.router)
app.include_router(libros.router)
app.include_router(copias.router)
app.include_router(lectores.router)
app.include_router(prestamos.router)
app.include_router(bioalert.router)


@app.get("/")
def root():
    return {
        "message": "Sistema de Biblioteca API",
        "endpoints": {
            "autores": "/autores",
            "libros": "/libros",
            "copias": "/copias",
            "lectores": "/lectores",
            "prestamos": "/prestamos",
            "bioalert": "/bioalert"
        },
        "docs": "/docs"
    }
