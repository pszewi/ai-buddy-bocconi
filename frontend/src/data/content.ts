export type Verticale =
  | 'relocation'
  | 'life_on_campus'
  | 'study_abroad'
  | 'career_readiness'

export type AskResponse = {
  answer: string
  sources: string[]
  verticale: Verticale
}

export type ChatTurn = {
  role: 'user' | 'assistant'
  content: string
}

export type RecentQuestion = {
  question: string
  verticale: Verticale
  count: number
  asked_at: number
}

export type SectionId =
  | 'conversation'
  | 'relocation'
  | 'life-on-campus'
  | 'study-abroad'
  | 'career-readiness'
  | 'trending'
  | 'about'

export type MenuItem = {
  id: SectionId
  label: string
  glyph:
    | 'chat'
    | 'relocation'
    | 'life_on_campus'
    | 'study_abroad'
    | 'career_readiness'
    | 'trending'
    | 'about'
}

export type Resource = {
  label: string
  url: string
}

export type VerticaleSectionContent = {
  id: SectionId
  verticale: Verticale
  heading: string
  primer: string
  examples: string[]
  resources: Resource[]
}

export const verticaleLabel: Record<Verticale, string> = {
  relocation: 'RELOCATION',
  life_on_campus: 'LIFE ON CAMPUS',
  study_abroad: 'STUDY ABROAD',
  career_readiness: 'CAREER READINESS',
}

export const menu: MenuItem[] = [
  { id: 'conversation', label: 'ask', glyph: 'chat' },
  { id: 'trending', label: 'trending', glyph: 'trending' },
  { id: 'relocation', label: 'relocation', glyph: 'relocation' },
  { id: 'life-on-campus', label: 'life on campus', glyph: 'life_on_campus' },
  { id: 'study-abroad', label: 'study abroad', glyph: 'study_abroad' },
  { id: 'career-readiness', label: 'career readiness', glyph: 'career_readiness' },
  { id: 'about', label: 'about', glyph: 'about' },
]

export const verticaleSections: VerticaleSectionContent[] = [
  {
    id: 'relocation',
    verticale: 'relocation',
    heading: 'relocation',
    primer:
      'Moving to Milan: housing, neighborhoods, transport, residence permits, codice fiscale, the SSN, and the practical first weeks of arrival.',
    examples: [
      'I am looking for a flat near Bocconi with a EUR700/month budget. Which neighborhoods would you recommend, and why?',
      'List the steps an international student must follow to register with Italy National Health Service in Milan.',
      'What is the price of an annual ATM transit pass for students under 27, and how does it compare with the standard adult annual urban pass?',
      'Which documents do I need to prepare before applying for the residence permit?',
      'How do I get from Malpensa to Milano Centrale on a student budget?',
    ],
    resources: [
      { label: 'Bocconi housing service', url: 'https://www.unibocconi.it/en/current-students/housing' },
      { label: 'ATM Milano student passes', url: 'https://www.atm.it/en/ViaggiaConNoi/Abbonamenti/Pages/Tipologie.aspx' },
      { label: 'Questura di Milano residence permit', url: 'https://questure.poliziadistato.it/it/Milano' },
      { label: 'Italian SSN registration', url: 'https://www.salute.gov.it/new/it/tema/iscrizione-al-ssn/' },
    ],
  },
  {
    id: 'life-on-campus',
    verticale: 'life_on_campus',
    heading: 'life on campus',
    primer:
      'Day-to-day at Bocconi: dining, library access, sport, student associations, wellbeing, counselling services, and campus events.',
    examples: [
      'Provide a structured table of dining areas available on the Bocconi campus.',
      'Quale documento devo portare per accedere alla Biblioteca Bocconi, e qual e la capienza massima dell edificio?',
      'How many different paid Bocconi Sport Membership tiers are listed for the 2025/2026 season?',
      'Which student associations focus on finance and consulting?',
      'What wellbeing services are available to international students?',
    ],
    resources: [
      { label: 'Library opening hours and access', url: 'https://www.unibocconi.it/en/current-students/library-archives/opening-hours' },
      { label: 'Bocconi Sport Center', url: 'https://www.bocconisport.eu/' },
      { label: 'Student associations directory', url: 'https://www.unibocconi.it/en/current-students/campus-life/student-activities/student-associations' },
      { label: 'Wellbeing and counselling', url: 'https://www.unibocconi.it/en/current-students/campus-life/counseling-self-empowerment-and-wellbeing/wellbeing' },
      { label: 'Campus map', url: 'https://www.unibocconi.it/en/campus/buildings-and-classrooms' },
    ],
  },
  {
    id: 'study-abroad',
    verticale: 'study_abroad',
    heading: 'study abroad',
    primer:
      'Exchange programs, double degrees, partner universities, summer schools, free-mover status, and international mobility rules.',
    examples: [
      'For the Bocconi MSc graduate Exchange Program selection score, how are academic GPA, credits, and Bachelor degree grade weighted?',
      'Which partner universities offer a Double Degree in Finance, and what are the requirements?',
      'When does the application window for next year exchange close?',
      'What is the application deadline for the Bocconi Double Degree program with MIT?',
      'Which summer schools are open to first-year MSc students?',
    ],
    resources: [
      { label: 'International mobility overview', url: 'https://www.unibocconi.it/en/international-mobility' },
      { label: 'Exchange programs', url: 'https://www.unibocconi.it/en/current-students/international-mobility/exchange-program' },
      { label: 'Double degree programs', url: 'https://www.unibocconi.it/en/current-students/international-mobility/double-degree-program' },
      { label: 'Bocconi summer schools', url: 'https://www.unibocconi.it/en/programs/summer-school' },
      { label: 'Farnesina country advisories', url: 'https://www.viaggiaresicuri.it/' },
    ],
  },
  {
    id: 'career-readiness',
    verticale: 'career_readiness',
    heading: 'career readiness',
    primer:
      'Career service, internships, CVs, scholarships, the Bocconi Merit Award, AlmaLaurea graduate surveys, and placement data.',
    examples: [
      'When does the curricular internship application close, and how do I submit it?',
      'What is the maximum amount of the Bocconi Merit Award tuition waiver for graduate students?',
      'What are the placement results published in the 2026 BESS graduate survey?',
      'Which industries hire most Bocconi MSc Finance graduates?',
      'How do I book a one-on-one with the Career Service?',
    ],
    resources: [
      { label: 'Career Services', url: 'https://www.unibocconi.it/en/current-students/career-services' },
      { label: 'Bocconi funding and scholarships', url: 'https://www.unibocconi.it/en/current-students/funding' },
      { label: 'AlmaLaurea graduate surveys', url: 'https://www2.almalaurea.it/cgi-php/universita/statistiche/framescheda.php' },
      { label: 'JobGate internships and offers', url: 'https://jobgate.unibocconi.it/' },
      { label: 'Bocconi Alumni Community', url: 'https://www.bocconialumni.it/' },
    ],
  },
]

export const trending: { count: number; question: string }[] = [
  { count: 12, question: 'How to apply for SSN as an international student' },
  { count: 9, question: 'MSc Finance prerequisites and language requirements' },
  { count: 7, question: 'Bocconi Sport membership tiers 2025/2026' },
  { count: 6, question: 'Library hours during the weekend' },
  { count: 5, question: 'Exchange application steps and deadlines' },
]

export const about = {
  heading: 'about',
  body:
    'A scholarly chatbot for Bocconi students, built for the Bocconi x Yellow Tech x OpenAI hackathon. The buddy answers from the bundled Bocconi knowledge base across four verticali and cites the source paths returned by the backend.',
}
