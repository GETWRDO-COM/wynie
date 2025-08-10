"use client";

import Header from "@/components/Header";
import Hero from "./Hero";
import Work from "./Work";
import Details from "./Details";
import Testimonials from "./Testimonials";
import Pricing from "./Pricing";
import Faq from "./Faq";
import Description from "./Description";
import Footer from "@/components/Footer";
import styles from "./Home.module.sass";

const HomePage = () => {
    return (
        <div className={styles.outer}>
            <Header />
            <Hero />
            <Work />
            <Details />
            <Testimonials />
            <Pricing />
            <Faq />
            <Description />
            <Footer />
        </div>
    );
};

export default HomePage;
