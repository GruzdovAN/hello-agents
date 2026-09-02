interface FallbackAlertProps {
  message: string
  isFallback: boolean
}

export function FallbackAlert({ message, isFallback }: FallbackAlertProps) {
  const show = isFallback || message.includes('Пониженный режим')
  if (!show) return null

  return (
    <div className="fallback-alert" role="alert">
      <strong>Режим пониженного качества</strong>
      <p>{message || 'Результат пониженного качества — только для справки.'}</p>
    </div>
  )
}
