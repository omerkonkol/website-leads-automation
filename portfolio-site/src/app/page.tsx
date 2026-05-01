import SmoothScroll from "@/components/SmoothScroll";
import Nav from "@/components/sections/Nav";
import Hero from "@/components/sections/Hero";
import StatsStrip from "@/components/sections/StatsStrip";
import Portfolio from "@/components/sections/Portfolio";
import Services from "@/components/sections/Services";
import TechMarquee from "@/components/sections/TechMarquee";
import Process from "@/components/sections/Process";
import Pricing from "@/components/sections/Pricing";
import Testimonials from "@/components/sections/Testimonials";
import Contact from "@/components/sections/Contact";
import Footer from "@/components/sections/Footer";
import WhatsAppFloat from "@/components/WhatsAppFloat";
import CookieConsent from "@/components/CookieConsent";

export default function Home() {
  return (
    <SmoothScroll>
      <Nav />
      <main>
        <Hero />
        <StatsStrip />
        <Portfolio />
        <Services />
        <TechMarquee />
        <Process />
        <Pricing />
        <Testimonials />
        <Contact />
      </main>
      <Footer />
      <WhatsAppFloat />
      <CookieConsent />
    </SmoothScroll>
  );
}
