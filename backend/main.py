from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from typing import Dict, List, Any
from pydantic import BaseModel

app = FastAPI()

# Настройка CORS для работы с React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # URL вашего React приложения
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище данных (в памяти)
data_store = {
    "df": None,
    "filtered_active": None,
    "data_by_dept": {}
}

LIMIT = 1000


class AnalysisResponse(BaseModel):
    initial_data: List[Dict[str, Any]]
    departments: List[str]
    department_data: Dict[str, List[Dict[str, Any]]]


def filter_by(column: str, value: str, dataframe: pd.DataFrame) -> pd.DataFrame:
    """Утилита для фильтрации данных"""
    return dataframe[dataframe[column] == value]


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Endpoint для загрузки CSV файла"""
    try:
        # Проверка типа файла
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Файл должен быть в формате CSV")
        
        # Чтение файла
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Сохранение в хранилище
        data_store["df"] = df
        
        # Обработка данных
        filtered_active = df[df['Status'] == 'Active'].head(LIMIT)
        data_store["filtered_active"] = filtered_active
        
        departments = df['Department'].unique().tolist()
        data_by_dept = {}
        
        for dep in departments:
            dept_data = filter_by('Department', dep, filtered_active)
            dept_data_sorted = dept_data.sort_values(
                by='Performance_Rating', 
                ascending=False
            ).head(100)
            data_by_dept[dep] = dept_data_sorted
        
        data_store["data_by_dept"] = data_by_dept
        
        return {
            "message": "Файл успешно загружен",
            "rows": len(df),
            "departments": departments
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")


@app.get("/api/analysis", response_model=AnalysisResponse)
async def get_analysis():
    """Endpoint для получения проанализированных данных"""
    if data_store["filtered_active"] is None:
        raise HTTPException(status_code=400, detail="Сначала загрузите CSV файл")
    
    try:
        # Подготовка данных для отправки
        initial_data = data_store["filtered_active"].head(5).to_dict('records')
        
        departments = list(data_store["data_by_dept"].keys())
        
        department_data = {}
        for dept, df in data_store["data_by_dept"].items():
            department_data[dept] = df.to_dict('records')
        
        return {
            "initial_data": initial_data,
            "departments": departments,
            "department_data": department_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")


@app.get("/api/department/{department_name}")
async def get_department_data(department_name: str):
    """Endpoint для получения данных конкретного департамента"""
    if data_store["data_by_dept"] is None or department_name not in data_store["data_by_dept"]:
        raise HTTPException(status_code=404, detail="Департамент не найден")
    
    dept_data = data_store["data_by_dept"][department_name]
    return {
        "department": department_name,
        "data": dept_data.to_dict('records')
    }


@app.get("/api/health")
async def health_check():
    """Проверка работоспособности API"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, 
                host="0.0.0.0", 
                port=8080, 
                proxy_headers=True,
                forwarded_allow_ips='*'  
            )