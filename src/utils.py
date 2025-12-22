def filter_by(column, column_value, data):
    res = data[data[column] == column_value]
    return res

# Читаем CSV файл
# df = pd.read_csv('src/hr.csv')
# filtered_active = df[df['Status'] == 'Active']

# departments = df['Department'].unique()

# print(departments)

# print(filter_by('Department', 'IT', filtered_active).head())

# Выведем первые строки таблицы
# print(filtered_active.head())
