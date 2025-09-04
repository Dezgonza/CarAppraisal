import { useState, useRef, useCallback } from 'react'
import './App.css'

function App() {
  // Modo de entrada: 'patente' o 'vehicle_data'
  const [inputMode, setInputMode] = useState('patente')
  
  // Campos para patente
  const [patente, setPatente] = useState('')
  
  // Campos para datos del vehículo
  const [brand, setMarca] = useState('')
  const [model, setModelo] = useState('')
  const [year, setAño] = useState('')
  const [version, setVersion] = useState('')
  
  // Campos comunes
  const [kilometers, setKilometros] = useState('')
  const [resultado, setResultado] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [progress, setProgress] = useState(null)
  const [useProgressMode, setUseProgressMode] = useState(true)
  
  const websocketRef = useRef(null)
  const sessionIdRef = useRef(null)

  const generateSessionId = () => {
    return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now()
  }

  const connectWebSocket = useCallback((sessionId) => {
    if (websocketRef.current) {
      websocketRef.current.close()
    }

    const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`)
    websocketRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const progressData = JSON.parse(event.data)
        setProgress(progressData)
      } catch (err) {
        console.error('Error parsing progress data:', err)
      }
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    return ws
  }, [])

  const validateForm = () => {
    if (inputMode === 'patente') {
      if (!patente.trim()) {
        setError('La patente es requerida')
        return false
      }
    } else {
      if (!brand.trim()) {
        setError('La brand es requerida')
        return false
      }
      if (!model.trim()) {
        setError('El model es requerido')
        return false
      }
      if (!year || parseInt(year) < 1990 || parseInt(year) > 2025) {
        setError('El year debe ser entre 1990 y 2025')
        return false
      }
    }
    return true
  }

  const buildRequestBody = (sessionId) => {
    const body = {
      session_id: sessionId,
      ...(kilometers && { kilometers: parseInt(kilometers) })
    }

    if (inputMode === 'patente') {
      body.patente = patente.trim()
    } else {
      body.vehicle_data = {
        brand: brand.trim(),
        model: model.trim(),
        year: parseInt(year),
        ...(version.trim() && { version: version.trim() })
      }
    }

    return body
  }

  const handleSubmitWithProgress = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setLoading(true)
    setError('')
    setResultado(null)
    setProgress(null)

    const sessionId = generateSessionId()
    sessionIdRef.current = sessionId

    // Conectar WebSocket para recibir progreso
    const ws = connectWebSocket(sessionId)

    try {
      const body = buildRequestBody(sessionId)
      const endpoint = useProgressMode ? '/valuar-con-progreso' : '/valuar'
      
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        throw new Error('Error al consultar la tasación')
      }

      const data = await response.json()
      setResultado(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
      setProgress(null)
      if (ws) {
        ws.close()
      }
    }
  }

  const handleSubmit = useProgressMode ? handleSubmitWithProgress : handleSubmitWithProgress

  const formatPrice = (price) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP'
    }).format(price)
  }

  return (
    <div className="app">
      <div className="container">
        <h1 className="title">Tasación de Automóviles</h1>
        
        <div className="input-mode-selector">
          <h3>¿Cómo quieres ingresar los datos del vehículo?</h3>
          <div className="radio-group">
            <label className="radio-label">
              <input
                type="radio"
                name="inputMode"
                value="patente"
                checked={inputMode === 'patente'}
                onChange={(e) => setInputMode(e.target.value)}
                disabled={loading}
              />
              <span>Por patente</span>
            </label>
            <label className="radio-label">
              <input
                type="radio"
                name="inputMode"
                value="vehicle_data"
                checked={inputMode === 'vehicle_data'}
                onChange={(e) => setInputMode(e.target.value)}
                disabled={loading}
              />
              <span>Por datos del vehículo</span>
            </label>
          </div>
        </div>

        <div className="progress-toggle">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={useProgressMode}
              onChange={(e) => setUseProgressMode(e.target.checked)}
              disabled={loading}
            />
            <span className="toggle-text">
              Mostrar progreso detallado
            </span>
          </label>
        </div>
        
        <form onSubmit={handleSubmit} className="form">
          {inputMode === 'patente' ? (
            <div className="field">
              <label htmlFor="patente">Patente del Vehículo *</label>
              <input
                type="text"
                id="patente"
                value={patente}
                onChange={(e) => setPatente(e.target.value.toUpperCase())}
                placeholder="Ej: ABC123"
                className="input"
                disabled={loading}
              />
            </div>
          ) : (
            <div className="vehicle-data-fields">
              <div className="field">
                <label htmlFor="brand">brand *</label>
                <input
                  type="text"
                  id="brand"
                  value={brand}
                  onChange={(e) => setMarca(e.target.value)}
                  placeholder="Ej: Toyota"
                  className="input"
                  disabled={loading}
                />
              </div>

              <div className="field">
                <label htmlFor="model">model *</label>
                <input
                  type="text"
                  id="model"
                  value={model}
                  onChange={(e) => setModelo(e.target.value)}
                  placeholder="Ej: Corolla"
                  className="input"
                  disabled={loading}
                />
              </div>

              <div className="field">
                <label htmlFor="year">year *</label>
                <input
                  type="number"
                  id="year"
                  value={year}
                  onChange={(e) => setAño(e.target.value)}
                  placeholder="Ej: 2020"
                  className="input"
                  disabled={loading}
                  min="1990"
                  max="2025"
                />
              </div>

              <div className="field">
                <label htmlFor="version">Versión (opcional)</label>
                <input
                  type="text"
                  id="version"
                  value={version}
                  onChange={(e) => setVersion(e.target.value)}
                  placeholder="Ej: XLI, GLX, etc."
                  className="input"
                  disabled={loading}
                />
              </div>
            </div>
          )}

          <div className="field">
            <label htmlFor="kilometers">Kilometraje (opcional)</label>
            <input
              type="number"
              id="kilometers"
              value={kilometers}
              onChange={(e) => setKilometros(e.target.value)}
              placeholder="Ej: 50000"
              className="input"
              disabled={loading}
              min="0"
            />
          </div>

          <button 
            type="submit" 
            className={`button ${loading ? 'loading' : ''}`}
            disabled={loading}
          >
            {loading ? 'Calculando...' : 'Calcular Tasación'}
          </button>
        </form>

        {error && (
          <div className="error">
            <p>{error}</p>
          </div>
        )}

        {progress && (
          <div className="progress-container">
            <h3>Progreso de la Tasación</h3>
            <div className="progress-bar-container">
              <div 
                className="progress-bar" 
                style={{ width: `${progress.percentage}%` }}
              ></div>
            </div>
            <div className="progress-info">
              <span className="progress-text">{progress.message}</span>
              <span className="progress-percentage">{Math.round(progress.percentage)}%</span>
            </div>
            <div className="progress-step">
              Paso {progress.step} de {progress.total_steps}
            </div>
          </div>
        )}

        {resultado && (
          <div className="result">
            <h2>Resultado de la Tasación</h2>
            <div className="result-content">
              {resultado.patente && (
                <div className="result-item">
                  <span className="label">Patente:</span>
                  <span className="value">{resultado.patente}</span>
                </div>
              )}
              
              {resultado.vehicle_data && (
                <>
                  <div className="result-item">
                    <span className="label">brand:</span>
                    <span className="value">{resultado.vehicle_data.brand}</span>
                  </div>
                  <div className="result-item">
                    <span className="label">model:</span>
                    <span className="value">{resultado.vehicle_data.model}</span>
                  </div>
                  <div className="result-item">
                    <span className="label">year:</span>
                    <span className="value">{resultado.vehicle_data.year}</span>
                  </div>
                  {resultado.vehicle_data.version && (
                    <div className="result-item">
                      <span className="label">Versión:</span>
                      <span className="value">{resultado.vehicle_data.version}</span>
                    </div>
                  )}
                </>
              )}
              
              <div className="result-item">
                <span className="label">Precio Estimado:</span>
                <span className="value price">{formatPrice(resultado.precio_estimado)}</span>
              </div>
              
              {resultado.precio_compra && (
                <div className="result-item">
                  <span className="label">Precio de Compra:</span>
                  <span className="value price">{formatPrice(resultado.precio_compra)}</span>
                </div>
              )}
              
              {resultado.kilometers && (
                <div className="result-item">
                  <span className="label">Kilometraje:</span>
                  <span className="value">{resultado.kilometers.toLocaleString()} km</span>
                </div>
              )}
              
              <div className="result-item">
                <span className="label">Observación:</span>
                <span className="value">{resultado.message}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
