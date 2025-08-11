import { useRef, useEffect, useState } from "react";
import * as THREE from "three";
import styles from "./Stars.module.sass";

type StarsProps = {};

const Stars = ({}: StarsProps) => {
    const mountRef = useRef<HTMLDivElement>(null);
    const [isReady, setIsReady] = useState(false);

    useEffect(() => {
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(
            75,
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );
        const renderer = new THREE.WebGLRenderer({ alpha: true });
        renderer.setSize(window.innerWidth, window.innerHeight);

        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d");
        if (context) {
            canvas.width = 32;
            canvas.height = 32;
            context.fillStyle = "white";
            context.beginPath();
            context.arc(16, 16, 16, 0, Math.PI * 2);
            context.fill();
        }

        const texture = new THREE.CanvasTexture(canvas);

        const geometry = new THREE.BufferGeometry();
        const vertices = [];
        for (let i = 0; i < 1000; i++) {
            vertices.push(
                Math.random() * 2000 - 1000,
                Math.random() * 2000 - 1000,
                Math.random() * 2000 - 1000
            );
        }
        geometry.setAttribute(
            "position",
            new THREE.Float32BufferAttribute(vertices, 3)
        );

        const material = new THREE.PointsMaterial({
            map: texture,
            size: 0.3,
            sizeAttenuation: true,
            transparent: true,
        });
        const stars = new THREE.Points(geometry, material);
        scene.add(stars);

        camera.position.z = 500;

        const animate = () => {
            requestAnimationFrame(animate);
            stars.rotation.y += 0.0005;
            renderer.render(scene, camera);
        };

        animate();

        setIsReady(true);

        if (mountRef.current) {
            mountRef.current.appendChild(renderer.domElement);
        }

        return () => {
            if (mountRef.current) {
                mountRef.current.removeChild(renderer.domElement);
            }
        };
    }, []);

    return (
        <div
            className={`${styles.stars} ${isReady ? styles.ready : ""}`}
            ref={mountRef}
        />
    );
};

export default Stars;
