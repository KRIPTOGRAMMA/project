from fastapi import APIRouter
from src.routes.auth import router as auth_router
from src.routes.users import router as users_router
from src.routes.workspaces import router as workspaces_router
# from src.routes.projects import router as projects_router
# from src.routes.tasks import router as tasks_router

main_router = APIRouter()

main_router.include_router(auth_router)
main_router.include_router(users_router)
main_router.include_router(workspaces_router)
# main_router.include_router(projects_router)
# main_router.include_router(tasks_router)
