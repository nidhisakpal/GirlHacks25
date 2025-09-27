import React from 'react'
import { BookOpen, Heart, Briefcase } from 'lucide-react'

interface Goddess {
  id: string
  name: string
  domain: string
  description: string
  icon: React.ReactNode
  color: string
}

const goddesses: Goddess[] = [
  {
    id: 'athena',
    name: 'Athena',
    domain: 'Academics & Wisdom',
    description: 'Goddess of wisdom, strategy, and academic excellence. She guides you through coursework, study strategies, and intellectual growth.',
    icon: <BookOpen className="w-8 h-8" />,
    color: 'athena'
  },
  {
    id: 'aphrodite',
    name: 'Aphrodite',
    domain: 'Well-being & Self-care',
    description: 'Goddess of love, beauty, and emotional wellness. She helps you balance life, manage stress, and nurture your mental health.',
    icon: <Heart className="w-8 h-8" />,
    color: 'aphrodite'
  },
  {
    id: 'hera',
    name: 'Hera',
    domain: 'Career & Leadership',
    description: 'Goddess of marriage, family, and power. She empowers you in career development, leadership skills, and professional growth.',
    icon: <Briefcase className="w-8 h-8" />,
    color: 'hera'
  }
]

const GoddessSelection: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Choose Your Divine Guide
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Each goddess offers unique wisdom tailored to your needs. Select the one that resonates with your current journey.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-8">
        {goddesses.map((goddess) => (
          <div
            key={goddess.id}
            className={`goddess-card ${goddess.color} cursor-pointer hover:scale-105`}
          >
            <div className="text-center mb-6">
              <div className={`text-goddess-${goddess.color} mb-4 flex justify-center`}>
                {goddess.icon}
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                {goddess.name}
              </h3>
              <p className={`text-goddess-${goddess.color} font-semibold mb-4`}>
                {goddess.domain}
              </p>
            </div>
            
            <p className="text-gray-700 text-center leading-relaxed">
              {goddess.description}
            </p>
            
            <div className="mt-6 text-center">
              <button
                className={`px-6 py-3 bg-goddess-${goddess.color} text-white rounded-lg font-semibold hover:opacity-90 transition-opacity`}
                onClick={() => {
                  // TODO: Implement goddess selection logic
                  console.log(`Selected ${goddess.name}`)
                }}
              >
                Choose {goddess.name}
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-12 text-center">
        <p className="text-gray-500 text-sm">
          Don't know which goddess to choose? Start chatting and Gaia will automatically match you with the most suitable guide.
        </p>
      </div>
    </div>
  )
}

export default GoddessSelection
