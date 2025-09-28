import { memo, useMemo } from 'react'

const baseStars = [
  { top: '6%', left: '6%', size: 6, opacity: 0.9 },
  { top: '8%', left: '92%', size: 7, opacity: 0.82 },
  { top: '12%', left: '18%', size: 5, opacity: 0.74 },
  { top: '14%', left: '32%', size: 5, opacity: 0.7 },
  { top: '18%', left: '62%', size: 6, opacity: 0.9 },
  { top: '22%', left: '82%', size: 5, opacity: 0.72 },
  { top: '24%', left: '68%', size: 8, opacity: 0.85 },
  { top: '26%', left: '42%', size: 6, opacity: 0.8 },
  { top: '28%', left: '12%', size: 4, opacity: 0.6 },
  { top: '30%', left: '30%', size: 4, opacity: 0.9 },
  { top: '32%', left: '58%', size: 5, opacity: 0.75 },
  { top: '34%', left: '76%', size: 5, opacity: 0.72 },
  { top: '36%', left: '78%', size: 6, opacity: 0.75 },
  { top: '38%', left: '72%', size: 7, opacity: 0.8 },
  { top: '40%', left: '24%', size: 5, opacity: 0.68 },
  { top: '42%', left: '34%', size: 6, opacity: 0.78 },
  { top: '45%', left: '64%', size: 4, opacity: 0.65 },
  { top: '46%', left: '82%', size: 4, opacity: 0.66 },
  { top: '48%', left: '80%', size: 5, opacity: 0.7 },
  { top: '50%', left: '38%', size: 4, opacity: 0.62 },
  { top: '52%', left: '18%', size: 4, opacity: 0.63 },
  { top: '54%', left: '70%', size: 5, opacity: 0.7 },
  { top: '58%', left: '46%', size: 5, opacity: 0.66 },
  { top: '62%', left: '74%', size: 4, opacity: 0.58 },
  { top: '86%', left: '14%', size: 5, opacity: 0.7 },
  { top: '90%', left: '8%', size: 6, opacity: 0.78 },
  { top: '88%', left: '88%', size: 7, opacity: 0.8 },
  { top: '92%', left: '76%', size: 5, opacity: 0.68 },
]

const createStarField = (count: number, idPrefix: string) =>
  Array.from({ length: count }, (_, index) => {
    const size = 15 + Math.random() * 10
    return {
      id: `${idPrefix}-${index}`,
      top: `${5 + Math.random() * 90}%`,
      left: `${5 + Math.random() * 90}%`,
      size,
      opacity: 0.35 + Math.random() * 0.4,
      blur: Math.random() > 0.7 ? 'drop-shadow(0 0 6px rgba(163, 201, 181, 0.5))' : 'drop-shadow(0 0 3px rgba(163, 201, 181, 0.4))',
    }
  })

const BackgroundShapes = () => {
  const sprinkleStars = useMemo(
    () => [
      ...createStarField(85, 'sprinkle-a'),
      ...createStarField(65, 'sprinkle-b'),
      ...createStarField(35, 'sprinkle-c'),
    ],
    [],
  )

  return (
    <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden" aria-hidden>
      <div className="absolute inset-0 bg-[#173b3b]" />

      <div
        className="absolute left-[-20%] top-[-8%] h-[50%] w-1/2 bg-[#6c977a]"
        style={{ clipPath: 'polygon(35% 0%, 100% 30%, 60% 100%, 0% 80%)' }}
      />
      <div
        className="absolute left-[-20%] bottom-[-25%] h-[80%] w-[55%] bg-[#4f7b63]"
        style={{ clipPath: 'polygon(20% 0%, 100% 25%, 80% 100%, 0% 75%)' }}
      />
      <div
        className="absolute right-[-15%] top-[-10%] h-[50%] w-[45%] bg-[#6c977a]"
        style={{ clipPath: 'polygon(0% 20%, 100% 0%, 80% 100%, 10% 80%)' }}
      />
      <div
        className="absolute right-[-22%] bottom-[-20%] h-[85%] w-[55%] bg-[#4f7b63]"
        style={{ clipPath: 'polygon(10% 0%, 100% 35%, 80% 100%, 0% 80%)' }}
      />

      {baseStars.map(({ top, left, size, opacity }, index) => (
        <Star key={`base-${index}`} top={top} left={left} size={size} opacity={opacity} />
      ))}
      {sprinkleStars.map(({ id, top, left, size, opacity, blur }) => (
        <Star key={id} top={top} left={left} size={size} opacity={opacity} blur={blur} subtle />
      ))}
    </div>
  )
}

export default memo(BackgroundShapes)

type StarProps = {
  top: string
  left: string
  size: number
  opacity: number
  blur?: string
  subtle?: boolean
}

const Star = ({ top, left, size, opacity, blur, subtle = false }: StarProps) => (
  <div
    className="absolute text-[#a3c9b5]"
    style={{
      top,
      left,
      width: size,
      height: size,
      opacity,
      filter: blur ?? 'drop-shadow(0 0 8px rgba(163, 201, 181, 0.55))',
      transform: subtle ? 'scale(0.85)' : 'scale(1)',
    }}
  >
    <svg viewBox="0 0 24 24" className="h-full w-full">
      <path
        fill="currentColor"
        d="M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8z"
      />
    </svg>
  </div>
)
