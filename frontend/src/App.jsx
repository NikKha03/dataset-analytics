import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Upload, FileText, TrendingUp } from 'lucide-react';
import './App.css';

const API_URL = 'http://localhost:8080/api';
// const API_URL = 'https://api.khalimendik.ru/api';

export default function App() {
	const [file, setFile] = useState(null);
	const [loading, setLoading] = useState(false);
	const [analysisData, setAnalysisData] = useState(null);
	const [error, setError] = useState(null);
	const [success, setSuccess] = useState(null);
	const [bonusData, setBonusData] = useState([]);
	const [loadingMore, setLoadingMore] = useState(false);
	const [hasMoreBonus, setHasMoreBonus] = useState(true);

	useEffect(() => {
		if (analysisData && bonusData.length === 0) {
			loadMoreBonus();
		} else if (bonusData.length !== 0) {
			setBonusData([]);
			loadMoreBonus();
		}
	}, [analysisData]);

	const handleFileChange = e => {
		const selectedFile = e.target.files[0];
		if (selectedFile && selectedFile.name.endsWith('.csv')) {
			setFile(selectedFile);
			setError(null);
			setSuccess(null);
		} else {
			setError('Пожалуйста, выберите CSV файл');
			setFile(null);
		}
	};

	const handleUpload = async () => {
		if (!file) {
			setError('Выберите файл для загрузки');
			return;
		}

		setLoading(true);
		setError(null);
		setSuccess(null);

		try {
			// Загрузка файла
			const formData = new FormData();
			formData.append('file', file);

			const uploadResponse = await fetch(`${API_URL}/upload`, {
				method: 'POST',
				body: formData,
			});

			if (!uploadResponse.ok) {
				const errorData = await uploadResponse.json();
				throw new Error(errorData.detail || 'Ошибка загрузки файла');
			}

			const uploadData = await uploadResponse.json();
			setSuccess(`Файл успешно загружен! Обработано строк: ${uploadData.rows}`);

			// Получение анализа
			const analysisResponse = await fetch(`${API_URL}/analysis`);
			if (!analysisResponse.ok) {
				throw new Error('Ошибка получения анализа');
			}

			const data = await analysisResponse.json();
			setAnalysisData(data);
		} catch (err) {
			console.log(err);
			setError(err.message);
			setAnalysisData(null);
		} finally {
			setLoading(false);
		}
	};

	const loadMoreBonus = async () => {
		setLoadingMore(true);

		try {
			const response = await fetch(`${API_URL}/load-more-bonus?load_with=${bonusData.length}`);

			if (!response.ok) {
				throw new Error('Ошибка получения данных с премией');
			}

			const data = await response.json();

			setBonusData(prevData => [...prevData, ...data.bonus_data]);
			setHasMoreBonus(data.has_more);
		} catch (err) {
			setError(err.message);
		} finally {
			setLoadingMore(false);
		}
	};

	return (
		<div className='app-container'>
			<div className='main-content'>
				<h1 className='main-title'>Анализ KPI и расчет вознаграждения</h1>

				{/* Секция загрузки файла */}
				<div className='card'>
					<h2 className='card-title'>
						<Upload size={24} />
						Загрузка данных
					</h2>

					<div className='upload-section'>
						<div className='file-input-wrapper'>
							<input type='file' accept='.csv' onChange={handleFileChange} className='file-input' />
						</div>

						<button onClick={handleUpload} disabled={!file || loading} className='upload-button'>
							{loading ? (
								<span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
									<span className='loader'></span>
									Загрузка...
								</span>
							) : (
								'Загрузить и проанализировать'
							)}
						</button>
					</div>
					{file && (
						<p style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#4a5568' }}>
							Выбран файл: <strong>{file.name}</strong>
						</p>
					)}

					{error && <div className='error-message'>⚠️ {error}</div>}

					{success && <div className='success-message'>✓ {success}</div>}
				</div>

				{/* Результаты анализа */}
				{analysisData && (
					<>
						{/* Таблица начальных данных */}
						<div className='card'>
							<h2 className='card-title'>
								<FileText size={24} />
								Таблица с начальными данными (первые 5 записей)
							</h2>

							<div className='table-container'>
								<table className='data-table'>
									<thead>
										<tr>{analysisData.initial_data[0] && Object.keys(analysisData.initial_data[0]).map(key => <th key={key}>{key.replace(/_/g, ' ')}</th>)}</tr>
									</thead>
									<tbody>
										{analysisData.initial_data.map((row, idx) => (
											<tr key={idx}>
												{Object.values(row).map((val, i) => (
													<td key={i}>{val !== null && val !== undefined ? String(val) : '-'}</td>
												))}
											</tr>
										))}
									</tbody>
								</table>
							</div>
						</div>

						{/* Таблица с бонусом */}
						<div className='card'>
							<h2 className='card-title'>
								<FileText size={24} />
								Таблица с рассчитанным вознаграждением
							</h2>
							<div className='scroll' style={{ paddingRight: '0.25rem', maxHeight: '600px', overflowY: 'auto' }}>
								<div className='table-container'>
									<table className='data-table'>
										<thead>
											<tr>{bonusData[0] && Object.keys(bonusData[0]).map(key => <th key={key}>{key.replace(/_/g, ' ')}</th>)}</tr>
										</thead>
										<tbody>
											{bonusData.map((row, idx) => (
												<tr key={idx}>
													{Object.values(row).map((val, i) => (
														<td key={i}>{val !== null && val !== undefined ? String(val) : '-'}</td>
													))}
												</tr>
											))}
										</tbody>
									</table>
								</div>
							</div>
							<button onClick={loadMoreBonus} className='upload-button' style={{ marginTop: '1rem' }}>
								Следующие 20 строк
							</button>
						</div>

						{/* Графики по департаментам */}
						<div className='charts-section'>
							<h2 className='section-title'>📊 KPI сотрудников по департаментам</h2>

							{analysisData.departments.map(dept => {
								const deptData = analysisData.department_data[dept] || [];
								const numberEmployees = analysisData.number_employees_by_dept[dept];
								const topEmployees = deptData.slice(0, 25);

								return (
									<div key={dept} className='chart-card'>
										<h3 className='chart-title'>Показатель KPI по сотрудникам отдела "{dept}"</h3>

										<div>
											<ResponsiveContainer width='100%' height={450}>
												<BarChart data={topEmployees} margin={{ left: 20 }}>
													<CartesianGrid strokeDasharray='3 3' stroke='#e2e8f0' />
													<XAxis dataKey='Full_Name' angle={-45} textAnchor='end' height={140} interval={0} tick={{ fontSize: 11, fill: '#2d3748' }} />
													<YAxis
														label={{
															value: 'Performance Rating',
															angle: -90,
															position: 'insideLeft',
															offset: -5,
															style: { fontSize: 14, fill: '#2d3748', fontWeight: '600' },
														}}
														tick={{ fontSize: 12, fill: '#2d3748' }}
														domain={[0, 'auto']}
														padding={{ top: 0 }}
													/>
													<Tooltip
														contentStyle={{
															backgroundColor: 'white',
															border: '2px solid #667eea',
															borderRadius: '8px',
															boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
															padding: '12px',
														}}
														labelStyle={{ color: '#2d3748', fontWeight: '600', marginBottom: '4px' }}
														itemStyle={{ color: '#4a5568' }}
													/>
													{/* <Legend wrapperStyle={{ paddingTop: '20px' }} iconType='rect' /> */}
													<Bar dataKey='Performance_Rating' fill='#667eea' name='KPI Rating' radius={[5, 5, 0, 0]} />
												</BarChart>
											</ResponsiveContainer>
										</div>

										<div style={{ marginTop: '0rem', fontSize: '0.875rem', color: '#718096' }}>
											<p>
												Всего сотрудников в отделе: <strong>{numberEmployees}</strong>
											</p>
											<p>
												Показано топ: <strong>{topEmployees.length}</strong> сотрудников
											</p>
										</div>
									</div>
								);
							})}
						</div>
					</>
				)}

				{!analysisData && !loading && (
					<div className='card empty-state'>
						<FileText size={64} style={{ margin: '0 auto 1rem', color: '#cbd5e0' }} />
						<h3 style={{ color: '#4a5568', marginBottom: '0.5rem' }}>Нет загруженных данных</h3>
						<p style={{ color: '#718096' }}>Загрузите CSV файл для начала анализа</p>
					</div>
				)}
			</div>
		</div>
	);
}
