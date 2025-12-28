from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from typing import Dict, List, Any
from pydantic import BaseModel

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище данных (в памяти)
data_store = {
    "df": None,
    "filtered_active": None,
    "data_by_dept": {},
    "number_employees_by_dept": {}
}

# Выбор конкретных столбцов
result_columns = ['Full_Name', 'Department', 'Performance_Rating', 'Experience_Years', 'Salary_INR', 'Bonus_Amount', 'Salary + Bonus']

class AnalysisResponse(BaseModel):
    initial_data: List[Dict[str, Any]]
    departments: List[str]
    department_data: Dict[str, List[Dict[str, Any]]]
    number_employees_by_dept: Dict[str, int]


def filter_by(column: str, value: str, dataframe: pd.DataFrame) -> pd.DataFrame:
    """Утилита для фильтрации данных"""
    return dataframe[dataframe[column] == value]

# 6. МАТРИЧНАЯ СИСТЕМА
def calculate_matrix_bonus(row):
    rating = row['Performance_Rating']
    exp = row['Experience_Years']
    if rating <= 2:
        percent = 0.05 if exp <= 2 else (0.07 if exp <= 5 else 0.08)
    elif rating == 3:
        percent = 0.10 if exp <= 2 else (0.12 if exp <= 5 else 0.15)
    else:  # rating >= 4
        percent = 0.15 if exp <= 2 else (0.20 if exp <= 5 else 0.25)
    return row['Salary_INR'] * percent

def calculate_full_bonus(row):
    salary = row['Salary_INR']
    bonus = row['Bonus_Amount']
    return round(salary + bonus, 2)


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
        data_store["df"] = df.head(5)
        
        # Обработка данных
        filtered_active = df[df['Status'] == 'Active']
        data_store["filtered_active"] = filtered_active
        
        departments = df['Department'].unique().tolist()
        data_by_dept = {}
        number_employees_by_dept = {}
        
        for dep in departments:
            dept_data = filter_by('Department', dep, filtered_active)
            dept_data_sorted = dept_data.sort_values(
                by='Performance_Rating', 
                ascending=False
            ).head(25)
            data_by_dept[dep] = dept_data_sorted
            number_employees_by_dept[dep] = len(dept_data)
        
        data_store["data_by_dept"] = data_by_dept
        data_store["number_employees_by_dept"] = number_employees_by_dept
        
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
        initial_data = data_store["df"].head(5).to_dict('records')
        departments = list(data_store["data_by_dept"].keys())
        
        department_data = {}
        for dept, df in data_store["data_by_dept"].items():
            department_data[dept] = df.to_dict('records')
        
        return {
            "initial_data": initial_data,
            "departments": departments,
            "department_data": department_data,
            "number_employees_by_dept": data_store["number_employees_by_dept"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")
    

@app.get("/api/load-more-bonus")
async def get_more_bonus(load_with: int = 0):
    """Endpoint для подгрузки строк с бонусом"""
    if data_store["filtered_active"] is None:
        raise HTTPException(status_code=400, detail="Сначала загрузите CSV файл")
    
    load_end = load_with + 20
      
    try:
        # Получаем срез данных
        df_slice = data_store["filtered_active"].iloc[load_with:load_end].copy()
        df_slice['Bonus_Amount'] = round(df_slice.apply(calculate_matrix_bonus, axis=1), 2)
        df_slice['Salary + Bonus'] = df_slice.apply(calculate_full_bonus, axis=1)
        
        # Выбираем нужные столбцы
        data = df_slice[result_columns].to_dict('records')
                
        return {
            "bonus_data": data,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")


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