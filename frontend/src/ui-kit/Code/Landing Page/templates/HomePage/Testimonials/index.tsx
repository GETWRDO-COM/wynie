import { useState } from "react";
import { Parallax } from "react-scroll-parallax";
import { Swiper, SwiperSlide } from "swiper/react";
import cn from "classnames";
import Image from "@/components/Image";
import Icon from "@/components/Icon";
import Head from "./Head";
import "swiper/css";
import "swiper/css/navigation";
import "swiper/css/thumbs";
import "swiper/css/pagination";
import styles from "./Testimonials.module.sass";

import { Navigation, Thumbs, Pagination } from "swiper/modules";

import { testimonials } from "@/mocks/testimonials";

type TestimonialsProps = {};

const Testimonials = ({}: TestimonialsProps) => {
    const [thumbsSwiper, setThumbsSwiper] = useState<any>(null);

    return (
        <div className={cn("section", styles.testimonials)}>
            <div className={cn("container", styles.container)}>
                <Head />
                <div className={styles.wrapper}>
                    <Image
                        className={styles.stars}
                        src="/images/testimonials-stars.svg"
                        width={785}
                        height={401}
                        alt=""
                    />
                    <div className={styles.wrap}>
                        <div className={styles.gradient}>
                            <Parallax className={styles.parallax} speed={-8}>
                                <Image
                                    className={styles.background}
                                    src="/images/gradient-3.png"
                                    fill
                                    alt=""
                                />
                            </Parallax>
                        </div>
                        <div className={styles.inner}>
                            <div className={styles.top}>
                                <Swiper
                                    className="swiper-testimonials-author"
                                    // initialSlide={2}
                                    navigation={{
                                        prevEl: ".swiper-arrow-prev",
                                        nextEl: ".swiper-arrow-next",
                                    }}
                                    pagination={{
                                        el: ".swiper-pagination-testimonials",
                                        // clickable: true,
                                    }}
                                    loop={true}
                                    speed={600}
                                    slidesPerView={1}
                                    spaceBetween={12}
                                    centeredSlides={true}
                                    thumbs={{ swiper: thumbsSwiper }}
                                    modules={[Navigation, Thumbs, Pagination]}
                                    breakpoints={{
                                        768: {
                                            slidesPerView: 3,
                                        },
                                    }}
                                >
                                    {testimonials.map((review) => (
                                        <SwiperSlide
                                            className={styles.user}
                                            key={review.id}
                                        >
                                            <div className={styles.avatar}>
                                                <Image
                                                    src={review.avatar}
                                                    width={44}
                                                    height={44}
                                                    alt=""
                                                />
                                            </div>
                                            <div className={styles.details}>
                                                <div className={styles.author}>
                                                    {review.author}
                                                </div>
                                                <div className={styles.post}>
                                                    {review.post}
                                                </div>
                                            </div>
                                        </SwiperSlide>
                                    ))}
                                </Swiper>
                            </div>
                            <div className={styles.body}>
                                <Swiper
                                    className="swiper-testimonials-content"
                                    spaceBetween={10}
                                    speed={500}
                                    onSwiper={setThumbsSwiper}
                                    modules={[Navigation, Thumbs, Pagination]}
                                    loop={true}
                                >
                                    {testimonials.map((review) => (
                                        <SwiperSlide
                                            className={styles.description}
                                            key={review.id}
                                        >
                                            <div className={styles.review}>
                                                <div className={styles.name}>
                                                    {review.title}
                                                </div>
                                                {review.content && (
                                                    <div
                                                        className={
                                                            styles.content
                                                        }
                                                    >
                                                        {review.content}
                                                    </div>
                                                )}
                                            </div>
                                        </SwiperSlide>
                                    ))}
                                </Swiper>
                            </div>
                        </div>
                    </div>
                </div>
                <div className={styles.foot}>
                    <div className={styles.control}>
                        <button
                            className={cn("swiper-arrow-prev", styles.arrow)}
                        >
                            <Icon name="arrow-prev" />
                        </button>
                        <div className={styles.pagination}>
                            <div
                                className={cn("swiper-pagination-testimonials")}
                            />
                        </div>
                        <button
                            className={cn("swiper-arrow-next", styles.arrow)}
                        >
                            <Icon name="arrow-next" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Testimonials;
