const COURSES = "maison.courses";
const FILE = "maison.file";

export async function api(chemin, options = {}) {
  const reponse = await fetch(chemin, {
    headers: options.corps instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...options,
    body: options.corps instanceof FormData ? options.corps : options.corps ? JSON.stringify(options.corps) : undefined,
  });
  if (!reponse.ok) {
    const corps = await reponse.json().catch(() => ({}));
    throw new Error(corps.detail || "Ça n'a pas fonctionné");
  }
  if (reponse.status === 204) return null;
  return reponse.json();
}

export function lireCoursesLocales() {
  const brut = localStorage.getItem(COURSES);
  return brut ? JSON.parse(brut) : [];
}

export async function chargerCourses() {
  try {
    const liste = await api("/api/courses");
    localStorage.setItem(COURSES, JSON.stringify(liste));
    await viderFile();
    return liste;
  } catch {
    return lireCoursesLocales();
  }
}

export async function cocherCourse(id, coche) {
  const liste = lireCoursesLocales().map((ligne) => ligne.id === id ? { ...ligne, coche } : ligne);
  localStorage.setItem(COURSES, JSON.stringify(liste));
  try {
    await api(`/api/courses/${id}`, { method: "PATCH", corps: { coche } });
  } catch {
    const file = JSON.parse(localStorage.getItem(FILE) || "[]");
    file.push({ id, coche });
    localStorage.setItem(FILE, JSON.stringify(file));
  }
  return liste;
}

async function viderFile() {
  const file = JSON.parse(localStorage.getItem(FILE) || "[]");
  if (!file.length) return;
  for (const action of file) {
    await api(`/api/courses/${action.id}`, { method: "PATCH", corps: { coche: action.coche } });
  }
  localStorage.removeItem(FILE);
}
